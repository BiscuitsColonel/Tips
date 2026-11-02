# WAL の書き込み量を測る方法と、pg_waldump で中身を覗くときの注意

一定時間にどれだけ WAL が出ているかを測る方法と、WAL ファイルの中身を `pg_waldump` と `strings` で覗くときに間違えやすい点のメモ。

（2021-07〜2021-09 時点のメモ。書き込み量の関数名は PostgreSQL 9.x のもの。PostgreSQL 10 で `pg_current_xlog_location` は `pg_current_wal_lsn`、`pg_xlog_location_diff` は `pg_wal_lsn_diff` に改名された。出典: [New in postgres 10](https://wiki.postgresql.org/wiki/New_in_postgres_10)、[Release 10](https://www.postgresql.org/docs/10/release-10.html)）

## 書き込み量を測る

現在の WAL 位置（LSN）を一定間隔で採取し、2 点の差をバイト数で求める。

```sql
-- PostgreSQL 10 以降（9.x は pg_current_xlog_location / pg_xlog_location_diff）
SELECT pg_current_wal_lsn();                       -- 例: 3/71E8D7F2 を一定間隔で採取
SELECT pg_wal_lsn_diff('3/71E8D7F2', '3/710AD780'); -- 後の位置, 前の位置 → バイト数
```

## WAL ファイルの中身を覗く

```sh
pg_waldump <WALファイル>
strings <WALファイル>
```

`pg_waldump` で間違えやすい点は次の 3 つ。

- サーバーが動いている間に実行すると、間違った結果になることがある
- 指定したタイムラインのレコードしか表示されない（指定しなければデフォルトのタイムラインだけ）。別のタイムラインのレコードは無視される
- 拡張子が `.partial` の WAL ファイルは読めない。読む必要があるときは、ファイル名から `.partial` を外してから渡す

PostgreSQL 9.x では、コマンド名が `pg_xlogdump` だった。
