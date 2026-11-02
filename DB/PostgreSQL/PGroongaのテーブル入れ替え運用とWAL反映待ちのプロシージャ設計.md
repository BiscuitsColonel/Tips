# PGroonga のインデックスを持つテーブルを入れ替えて更新する運用と、壊れたときの掃除、レプリカへの WAL 反映待ち

全文検索に PGroonga を使うテーブルを、検索を止めずに更新するために書いたプロシージャの設計メモ。使われなくなった側のテーブルへ差分だけ反映する、2 枚のテーブルを入れ替える、PGroonga の内部エラーを検知して掃除する、レプリカが追いつくのを待つ、の 4 つ。

（2021-03 時点のメモ。PGroonga と PostgreSQL のバージョンは元メモに記載なし。テーブル名・ロール名・ホストは仮の名前に置き換えた）

## 入れ替えで使われなくなった側は、インデックスを落として差分だけ反映する

検索用と更新用の 2 枚のテーブルを持ち、名前を入れ替えて切り替える。入れ替えのあと、使われなくなった側のテーブルは PGroonga のインデックスを落とし、稼働側との差分だけを反映して次の入れ替えに備える。全件を入れ直さず、変わった行だけを書く。

```sql
-- 稼働側 (live) にあって対象 (stale) に無い行を消す
DELETE FROM stale WHERE (key) IN (SELECT key FROM stale WHERE (key) NOT IN (SELECT key FROM live));

-- 差分があった行だけを UPSERT する。EXCEPT で「完全に同じ行」を除くのが肝
INSERT INTO stale
SELECT * FROM live EXCEPT SELECT * FROM stale
ON CONFLICT (key) DO UPDATE SET (col1, col2, col3) = (EXCLUDED.col1, EXCLUDED.col2, EXCLUDED.col3);
```

元のプロシージャは、これを動的 SQL で組み立てた。列の一覧は `information_schema.columns` から作り、`SET (列) = (EXCLUDED.列)` の左右の形を `EXCLUDED.` の付け外しで作っていた。落とすインデックスの名前は `pg_class` / `pg_index` / `pg_attribute` を結んで、テーブルと PGroonga 列から引く。差分反映のあとに PGroonga のインデックスを張り直す手順は、元メモには含まれていない。

## 使われていない側と入れ替える

更新が済んだテーブルを稼働させるため、名前を入れ替える。切り替える前に、全ホストで稼働中のテーブルにロックが無いことを確かめる。

```sql
-- ホストごとに dblink で確認する。ロックを持つ数が全ホストの合計で 0 のときだけ入れ替える
SELECT cnt FROM dblink('hostaddr=<ホスト> port=<ポート> dbname=<DB> user=<ユーザー>',
  'SELECT COUNT(1) FROM pg_locks l LEFT JOIN pg_class c ON l.relation = c.oid
    WHERE c.relname = ''<稼働中のテーブル>''') AS t(cnt int);

ALTER TABLE main RENAME TO tmp_tbl;
ALTER TABLE sub  RENAME TO main;
ALTER TABLE tmp_tbl RENAME TO sub;
DROP INDEX <使われなくなった側の PGroonga インデックス>;
```

ホストの一覧は配列で受けて `FOREACH ... IN ARRAY` で回す。ロックが 1 つでも残っていれば入れ替えず、全ホストの確認をやり直す。元の実装は待機を挟まずに繰り返すので、使うなら `pg_sleep` を足す。

## PGroonga の内部エラーを検知して、壊れたオブジェクトを消す

PGroonga のインデックスを一度引き、内部エラー（SQLSTATE `58000`）が出たら、メッセージの中から壊れたオブジェクト名を取り出して強制削除し、`pgroonga_vacuum()` を呼び直す。

```sql
BEGIN
  PERFORM * FROM <テーブル> WHERE <列> &@ '' LIMIT 0;   -- インデックスを触るだけの空振りクエリ
  PERFORM pgroonga_vacuum();
EXCEPTION WHEN SQLSTATE '58000' THEN
  GET STACKED DIAGNOSTICS v_text = MESSAGE_TEXT;
  v_name := substring(v_text from '<([^<>]*)>');        -- メッセージ中の <...> がオブジェクト名
  PERFORM pgroonga_command('object_remove', ARRAY['name', v_name, 'force', 'yes']);
  PERFORM pgroonga_vacuum();
END;
```

エラーメッセージの中の `<名前>` を正規表現で取り出す、というのが元の実装の勘所。壊れたものを削除したあとにもう一度インデックスを引き直して、直ったかを確かめていた。

## レプリカへの WAL 反映待ち

入れ替えやリロードの前に、スタンバイが追いつくまで待つ。`pg_stat_replication` の送信済み位置と、書き込み・フラッシュ・反映の各位置の差が 0 になるまでループする。

```sql
CREATE OR REPLACE PROCEDURE wal_wait() LANGUAGE plpgsql AS $$
DECLARE diff_check numeric;
BEGIN
  LOOP
    SELECT ((a + b + c) / 3)::numeric(1000, 0) INTO diff_check
    FROM (SELECT pg_wal_lsn_diff(sent_lsn, write_lsn)  a,
                 pg_wal_lsn_diff(sent_lsn, flush_lsn)  b,
                 pg_wal_lsn_diff(sent_lsn, replay_lsn) c
          FROM pg_stat_replication) lsn;
    IF diff_check = 0 THEN EXIT; END IF;
    RAISE INFO '未適用 WAL が % あるため 10 秒待機します', diff_check;
    PERFORM pg_sleep(10);
  END LOOP;
END; $$;
```

この実装をそのまま使うときの落とし穴（コードを読んだ限りの指摘で、実機での検証はしていない）。

- スタンバイが 1 台も接続していないと `pg_stat_replication` が空になり、`diff_check` が NULL のまま `IF diff_check = 0` が成立せず、永久に待つ
- `SELECT INTO` は先頭の 1 行しか取らないので、スタンバイが複数いても 1 台分しか見ない
