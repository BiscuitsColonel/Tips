# PGroonga のインデックスを、レプリケーション構成で別テーブルに作ってから名前を入れ替えて作り直す手順

PGroonga（全文検索の拡張）のインデックスを、読み取りを止めずに作り直すために組んだ手順とスクリプトの設計メモ。導入手順や検索構文は [PGroonga の公式ページ](https://pgroonga.github.io/ja/) を見る。

（2021-06 時点のメモ。PGroonga 2.2 系。手順中で `CALL` を使うので PostgreSQL 11 以降。メモにはこの手順を流した結果のログは残っていないので、動作確認済みとは書かない）

## 考え方

- 稼働中のテーブル（`pgrn_tbl`）には触らず、同じ構造の保守用テーブル（`pgrn_tbl_maintenance`、`CREATE TABLE ... (LIKE pgrn_tbl INCLUDING ALL)` で作る）に新しい PGroonga インデックスを作る。
- 作ったインデックスの WAL がスタンバイに届き、適用されたことを確認してから、2 つのテーブル名を入れ替える。
- 入れ替えの後は、旧テーブル側の古いインデックスを落として中身を作り直し、次回の保守用に備える。
- 保守専用ユーザーが DDL を直接叩かなくて済むよう、各操作を `SECURITY DEFINER` のプロシージャにして、所有者を管理者ロールにする。

PGroonga の WAL は `pgroonga.enable_wal = on` で出す。スタンバイ側は `hot_standby_feedback = on`、保守を回す側の `synchronous_commit = local` とした。

## プロシージャ

名前の入れ替えと、インデックスの作成。他に、インデックス名を受けて `REINDEX INDEX` する `reindex`、旧インデックスを `DROP INDEX` したうえで保守用テーブルを `TRUNCATE` して稼働中テーブルから `INSERT ... SELECT` し直す `update` を同じ形で作った。

```sql
CREATE OR REPLACE PROCEDURE pgrn_tbl_rename(main_tbl text, sub_tbl text)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE 'ALTER TABLE ' || main_tbl || ' RENAME TO tmp_tbl';
    EXECUTE 'ALTER TABLE ' || sub_tbl  || ' RENAME TO ' || main_tbl;
    EXECUTE 'ALTER TABLE tmp_tbl RENAME TO ' || sub_tbl;
END;
$$;
ALTER PROCEDURE pgrn_tbl_rename(text, text) OWNER TO postgres;

CREATE OR REPLACE PROCEDURE pgrn_tbl_maintenance_pgroonga_createindex(sub_tbl text, pgrn_column text, pgrn_idx text)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE 'CREATE INDEX ' || pgrn_idx || ' ON ' || sub_tbl || ' USING pgroonga(' || pgrn_column || ')';
END;
$$;
ALTER PROCEDURE pgrn_tbl_maintenance_pgroonga_createindex(text, text, text) OWNER TO postgres;
```

## スタンバイ側で WAL を適用させるプロシージャ

スタンバイでは、`wal_apply` というプロシージャを作り、`SELECT * FROM <tbl> WHERE <col> &@ '' LIMIT 0` のように 0 件のクエリでインデックスを触らせて、PGroonga の WAL を適用させる作りにした（PGroonga の WAL は検索などでインデックスに触れたときに適用される、という前提で組んだもの。この前提も、0 件のクエリで実際に適用されることも、公式ドキュメントでは未確認で、動作確認の記録も無い）。`pgroonga_vacuum()` を呼ぶ分岐も同じプロシージャに持たせた。

## 手順の流れ（マスターで回すシェルスクリプトの骨格）

1. 事前確認。全スタンバイに接続できるか（5 秒間隔で 10 回までリトライ）、いま稼働中テーブルに付いている PGroonga インデックス名の末尾の数字を読み、次の名前を `+1`（10 になったら 0）で決める。インデックス名は `<名前><数字>` で世代を持たせる。
2. マスターで保守用テーブルに新しいインデックスを作る。
3. 作成で出た WAL が全スタンバイに届くまで待つ。マスターの `pg_current_wal_lsn()` と、各スタンバイの `pg_last_wal_receive_lsn()` の差（`pg_wal_lsn_diff`）が 0 になるまで 5 秒間隔で見る。`pg_last_wal_receive_lsn()` は PostgreSQL の WAL を受信した位置であり、PGroonga 側への適用が済んだことは示さない。適用は次の手順 4 に任せている（動作確認の記録は無い）。
4. スタンバイで `wal_apply` を実行し、PGroonga の WAL を適用させる想定（適用されることは未確認）。
5. 稼働中テーブルと保守用テーブルの名前を入れ替える（`rename`）。
6. 入れ替えで出た WAL がスタンバイに届くまで待つ。
7. 入れ替え後に保守用側になった旧テーブルの中身を、稼働中テーブルと同じに作り直す（`update`）。
8. 再び WAL の到達を待ち、スタンバイで `pgroonga_vacuum()` を呼ぶ `wal_apply` を実行して、旧インデックスの残りを片付ける。

## 手順 4 と 8 でスタンバイの WAL 適用が失敗したとき

スクリプトは、スタンバイで `wal_apply` が失敗したらエラー文から `Sources<数字>` を抜き出す。これは Groonga 側のテーブル名で、エラー文に出ていた。次の順に直す作りにした。

1. `pgroonga_command('table_list')` にその名前が残っているあいだ、`pgroonga_command('object_remove', ARRAY['name', '<Sources名>', 'force', 'yes'])` で Groonga のテーブルを消す。
2. マスターで該当インデックスを `REINDEX` する。
3. スタンバイで `wal_apply` をもう一度流す。成功するまで、上限回数までこれを繰り返す。

## 検証用の負荷の掛け方

保守中に読み取りが失敗しないかは、スタンバイに `pgbench -n -f select.sql -c 30 -j 2 -T 100` を連続で流し、終了コードが 0 でなくなった時刻を出す形で見ようとした。マスター側は、更新用 SQL（`\gset` でランダムなキーを取って `UPDATE`、続けて `INSERT` と `DELETE`）を `-c 1` の `pgbench` で流し、そのあとに保守スクリプトを呼ぶ、を繰り返した。
