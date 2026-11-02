# PostgreSQL 12 のレプリケーションで試した、フェイルオーバー後の切り戻しと、論理レプリケーションが競合で止まったときの読み飛ばし

ストリーミングレプリケーションで旧プライマリを `pg_rewind` で戻した順序と、論理レプリケーションで主キー重複が起きたときの挙動と対処を、実際に流して残したメモ。構築手順そのものは公式ドキュメントを見る。

（2021-10 時点のメモ。PostgreSQL 12（ストリーミング側は 12.8）、CentOS 7 の検証機で確認。ホスト名・IP・ユーザー名は仮のもの）

## ストリーミングレプリケーション: プライマリ障害から旧プライマリを戻すまで

前提は、物理レプリケーションスロットを使う非同期構成、`wal_log_hints = on`（`pg_rewind` に必要）、`hot_standby_feedback = on`、WAL アーカイブあり。

順序に意味があるのは次のところ。

1. プライマリ障害は `kill -9` でプロセスを落として再現し、スタンバイで `pg_ctl promote` する。
2. 旧プライマリは、いったん起動してから正常停止し直す。クラッシュしたままでは `pg_rewind` に進めない。
3. 旧プライマリを起動している間に、旧プライマリに残っているレプリケーションスロットを `pg_drop_replication_slot()` で消す。残したままスタンバイとして戻すと、スロットが WAL を抱えたままになり、WAL が溜まってディスクを圧迫するとメモに書いてある。
4. 旧プライマリを止めて、新プライマリを元にして `pg_rewind` を流す。

```sh
pg_rewind -D $PGDATA --source-server="host=<新プライマリ> port=5432 user=postgres dbname=postgres"
```

5. 新プライマリに、旧プライマリ用の物理スロットを別名で作る（`pg_create_physical_replication_slot('node_b_slot')`）。
6. 旧プライマリの `postgresql.auto.conf` に `primary_conninfo`（レプリケーション用ユーザーと `passfile`）と `primary_slot_name` を書き、`$PGDATA/standby.signal` を作ってから起動する。

起動後のログに、WAL の末尾で `file not found` が出たり、`00000002.history` が無いというエラーが出たりするが、切り戻しとして正常な挙動だとメモに書いてある。

別の注意として、CentOS 7 に PostgreSQL 12 を `yum` で入れたとき、`openssl` のパッケージが無いとレプリケーションが確立しないことがあった、とメモにある（メモに原因の記載はなく、この件は再確認していない）。

## 論理レプリケーション: 主キー重複で止まったとき

パブリケーション側（プライマリ）で `wal_level = logical` にし、`CREATE PUBLICATION`、サブスクライバー側（スタンバイ）で `CREATE SUBSCRIPTION` を作る。スロットは先に自分で `pg_create_logical_replication_slot('node_a_slot', 'pgoutput')` で作り、サブスクリプションを `create_slot = false, slot_name = 'node_a_slot'` で結びつけた。

サブスクライバー側に先に `id = 4` を入れておき、パブリケーション側で `id = 4` と `id = 5` を続けて INSERT した結果は次のとおり。

- サブスクライバーのログに `duplicate key value violates unique constraint` が出る。
- サブスクライバーには `id = 4` までしか無く（`4` はサブスクライバー自身が先に入れた行）、パブリケーション側で入れた `id = 5` も届かない。競合したトランザクションで適用が止まり、後ろに続く更新も待たされたまま。
- 自動では読み飛ばされない。直す方法は 2 つ試した。

### 方法 1: サブスクライバー側の衝突している行を消す

`DELETE FROM test_tbl WHERE id = 4;` を流すと、止まっていたトランザクションが適用され、`id = 4, 5` が揃う（パブリケーション側と同じ 5 行になった）。

### 方法 2: 衝突したトランザクションを読み飛ばす

サブスクライバー側の行は残したいときに使う。どこまで進めればよいかを知るために、論理スロットを `test_decoding` でコピーして、未適用の変更の中身と LSN を見る。コピーなら本物のスロットの読み取り位置は進まない。

```sql
-- パブリケーション側で実行
SELECT pg_copy_logical_replication_slot('node_a_slot', 'copy_slot', true, 'test_decoding');
SELECT * FROM pg_logical_slot_get_changes('copy_slot', NULL, NULL);
```

出力の例（XID と LSN は実行時のもの）。

```text
 0/16CFBA8 | 568 | BEGIN 568
 0/16CFBA8 | 568 | table public.test_tbl: INSERT: id[integer]:4 val[text]:'test_val4'
 0/16CFC60 | 568 | COMMIT 568
 0/16CFD10 | 569 | BEGIN 569
 0/16CFD10 | 569 | table public.test_tbl: INSERT: id[integer]:5 val[text]:'test_val5'
 0/16D0748 | 569 | COMMIT 569
```

サブスクライバー側で、サブスクリプションに対応するレプリケーションオリジン名（`pg_replication_origin` の `roname`、例では `pg_16399`）を調べ、`pg_replication_origin_advance` で位置を進める。

```sql
SELECT * FROM pg_replication_origin;
SELECT pg_replication_origin_advance('pg_16399', '0/16CFD10'::pg_lsn);
```

この例では、失敗した 568 の COMMIT 行（`0/16CFC60`）の次のトランザクションの BEGIN 行の LSN（`0/16CFD10`）を指定した。その結果、サブスクライバーには `id = 5` が適用され、自分で入れた `id = 4` もそのまま残った（`1, 2, 3, 5, 4` の 5 行）。指定する LSN は、失敗したトランザクションの COMMIT より後ろにする。

使い終わった `copy_slot` は一時スロット（`true` で作成）なのでセッションが切れれば消えるが、パブリケーション側では `pg_replication_slots` で残っていないことを確認する。
