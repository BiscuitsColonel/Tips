# VACUUM のログの読み違えと、ロック・排他まわりの挙動メモ

autovacuum のログの読み方、VACUUM FULL 周りの意外な挙動、pg_locks の見え方、パーティションテーブルのロックについて、サポート問い合わせで分かったことをまとめたメモ。

（2020〜2021 年ごろのサポート問い合わせの記録。PostgreSQL 10〜12）

## autovacuum のログで `maintenance_work_mem` の不足を判定する

autovacuum が完了したときのログ `automatic vacuum of table "...": index scans: N` の `N` を見る。2 以上なら、デッドタプルの記録用メモリが足りず、インデックススキャンが複数回に分かれている。1 なら足りている。メモリは `autovacuum_work_mem`、未設定（-1）なら `maintenance_work_mem` が上限。

## ログの `oldest xmin` はプロセス ID ではない

`oldest xmin: 573844456` はプロセスではなく、VACUUM 開始時点で動いていた最も古いトランザクション ID。これが古いまま進まないとデッドタプルが回収されない。どのセッションかは `pg_stat_activity` の `backend_xmin` や `xact_start` で探す。

## 通常の VACUUM も WAL を出す

「VACUUM FULL だけが WAL を出す」ではない。通常の VACUUM も、インデックスエントリの削除、ページの整理、可視性マップの更新に伴う WAL を出す。レプリカやリカバリに「VACUUM を実行したこと」が反映されるのはそのため。WAL を出さずに VACUUM FULL をする方法は無い。

## VACUUM FULL の直後の VACUUM が遅い

VACUUM は可視性マップで「全タプルが全員から見える」ページを読み飛ばす。VACUUM FULL をするとテーブル全ページの可視性マップが立っていない状態になり、直後の通常 VACUUM は全ページを走査する。2 回目からは変更のあったページだけに戻って短くなる。

## VACUUM FULL 中のディスクフル

`PANIC: could not write to file "pg_wal/xlogtemp.NNN": No space left on device` が出てプロセスが落ちる。VACUUM FULL は新しいファイルへ書き直す分の空きが要るうえ、WAL も出す。空きを作るか、テーブルスペースで別のディスクにテーブルやインデックスを置く。

## `55P03 lock_not_available` は autovacuum でも出る

`lock_timeout = 0`（無効）でも、`LOG: skipping vacuum of "..." --- lock not available` や `skipping analyze of ...` として 55P03 が出る。autovacuum や自動 ANALYZE がテーブルのロックを取れずに諦めたときのログで、明示的なロック指定（NOWAIT など）だけが原因ではない。このエラーコードは行ロックに限らずテーブルロックの失敗でも使われる。特定のメッセージだけをログから消す設定は無く、深刻度レベル単位でしか制御できない。

## pg_locks の `tuple` が AccessExclusiveLock に見える

`SELECT FOR UPDATE` や `DELETE` が行ロックのレベルで競合すると、`locktype = tuple, mode = AccessExclusiveLock` の行が現れる。これは行ロックを取る過程で一時的に取る内部ロックで、行ロックが取れた時点で（トランザクションの終了を待たず）解放される。待ちが出ているときだけ見える。

- 行ロックは SELECT と競合しないので、このロックがあっても SELECT は待たされない。
- 行ロックのモードと、`tuple` ロックに表示されるモードの対応は次のとおり。`relation` のロックとは競合しない。

| 行ロックのモード | 表示されるモード |
| --- | --- |
| KEY SHARE | AccessShareLock |
| SHARE | RowShareLock |
| NO KEY UPDATE | ExclusiveLock |
| FOR UPDATE | AccessExclusiveLock |

## 親テーブル経由の操作は全子テーブルのロックを取る

- 現象・条件: パーティションの親テーブルを通して特定の子だけを参照・更新しているときに、別の子へ `REINDEX` をかけたら待たされた。
- 分かったこと: 親を通した時点で全子テーブルに `AccessShareLock` が取られる。そのため無関係の子の `REINDEX` と競合する。
- 対処: `REINDEX ... CONCURRENTLY`（12 以降）なら競合しない。ただし失敗する可能性があり、通常の `REINDEX` より時間がかかる。更新側を、親ではなく子テーブルに直接アクセスするように変えれば他の子のロックは取られない。

## テーブルスペースの置き場所を変える（DB 自体のテーブルスペースではない場合）

ディスクのマウント先を差し替えたいとき、ファイルを入れ替えるコピーより、SQL で一時テーブルスペースへ退避して戻すほうが安全、というのがサポートの案内。

1. 退避用ディレクトリ（移動対象が入る空き容量が必要）とテーブルスペースを作る
2. `ALTER TABLE ALL IN TABLESPACE 元 SET TABLESPACE 退避先;` と `ALTER INDEX ALL IN TABLESPACE ...` で移す
3. 元のテーブルスペースを `DROP`、マウント先を差し替え（fstab 修正と再起動、または停止して umount と `mount -a`）
4. 同名でテーブルスペースを作り直し、2 と逆向きに戻して、退避用を `DROP`

移動中は強いロックが取られる。手順は、`CREATE DATABASE` の時点でデータベース自体を外部のテーブルスペースに置いている場合には使えない。システムカタログもそこに載るため。その場合は停止してファイルごとコピーするしかない。
