# pg_statsinfo と pg_dbms_stats で踏んだ点（リポジトリ肥大・不正文字のループ・スキーマ不在）

統計情報の収集拡張 pg_statsinfo（スナップショットをリポジトリ DB に貯める）と、実行計画を固定する pg_dbms_stats について、サポート問い合わせで分かったことをまとめたメモ。

（2020〜2021 年ごろのサポート問い合わせの記録。PostgreSQL 10〜11 前後）

## 不正な文字列でエラーログの記録がループして I/O が増える

- 現象: DB の応答が遅くなり、OS 再起動で直った。ログに次のエラーが再起動まで繰り返し出ていた。

```text
ERROR:  pg_statsinfo: query failed: ERROR:  invalid byte sequence for encoding "UTF8": 0x..
DETAIL:  query was: INSERT INTO statsrepo.log VALUES ($1, ...
```

- 分かったこと: 次のループが回っていた。(1) 不正なバイト列を含む SQL がエラーになる、(2) pg_statsinfo がそのエラーログを拾う、(3) エラーログを `statsrepo.log` に入れようとするが、同じ不正バイトを含むので再びエラー、(4) それをまた拾う。この繰り返しのログ出力でディスク I/O が増え、他の処理が遅れた。
- 対処: クライアントと DB サーバーの文字エンコーディングを揃える。きっかけの SQL を探すには、エラーが出始める前のログファイルを `head` で見て、エラーを含まない最初のファイルとその前後を調べる。

## 100MB 級の SQL がスナップショットに入り続ける

- 現象: 巨大な SQL のせいで、`pg_statsinfo.snapshot_interval` の間隔でリポジトリの `statsrepo.statement` に毎回その SQL が入り、ネットワークとディスクを圧迫した。
- 分かったこと:
  - `pg_statsinfo.repository_keepday` はスナップショット自体の保持日数。特定の SQL の情報だけが消えて収集されなくなるわけではない。
  - DB・ユーザー単位で収集対象から外す設定はあるが、SQL（QueryID）単位では外せない。蓄積済みスナップショットから特定の SQL だけを消すこともできない。
- 対処:
  - SQL 本文を VIEW に入れて、実行する SQL を `SELECT * FROM view` にする。スナップショットに入る本文が小さくなる。
  - 容量を空けたいときは、リポジトリ側で `SELECT statsinfo.maintenance('2020-11-01 00:00:00'::timestamptz);` を実行する。引数より古いスナップショットが消え、`statsrepo.statement` の分も減る。
  - 監視対象側の `pg_stat_statements` はこの関数では消えないので、次のスナップショットで再びリポジトリに入りうる。`pg_stat_statements_reset()` は有効（全 SQL の情報が消える）。`pg_statsinfo.stat_statements_max` を一時的に 0 や小さい値にするのは効かない。これは `pg_stat_statements` の保持数ではなく、リポジトリへ送る SQL 数（負荷の高い順）の上限だから。`pg_statsinfo.stat_statements_exclude_users` に、その SQL を実行したユーザーを入れるのは有効。外すと再び送られる。

## 蓄積ログの削除で `out of shared memory`（53200）

- 現象: 毎日の削除処理が `WARNING: out of shared memory`（`DROP TABLE IF EXISTS statsrepo.log_YYYYMMDD`）で失敗した。
- 分かったこと: 日次のログテーブル（パーティション）を多数一度に消すと、1 トランザクションで取るロックが `max_locks_per_transaction` の枠を超える。
- 対処: リポジトリ DB 側で `SELECT statsrepo.del_repolog2('2020-12-01 09:00:00'::timestamptz);` を使うと、引数より古い蓄積ログを手動で消せる。保持日数（`pg_statsinfo.repolog_keepday`）を延ばして一度に消す量を減らす方法もある。

## `schema "dbms_stats" does not exist`

- 現象・条件: `shared_preload_libraries` に `pg_dbms_stats` を入れていて、`CREATE EXTENSION pg_dbms_stats` をしていないデータベース（例: `postgres`）で SELECT すると出る。pg_statsinfo は起動時に同じエラーを出して fallback mode で起動する。
- 分かったこと: preload でライブラリはどの DB でも読み込まれるが、スキーマは `CREATE EXTENSION` をした DB にしか無い。リポジトリのスキーマ（`statsrepo`）が無いために起きるエラーではない。
- 対処は 3 つ。
  1. 該当 DB でも `CREATE EXTENSION pg_dbms_stats;` を実行する。
  2. セッションで `SET pg_dbms_stats.use_locked_stats = off;` にして無効化する。
  3. `shared_preload_libraries` から外し、使う DB のセッション開始ごとに `LOAD pg_dbms_stats;` を実行する。
- preload に書かない場合、`CREATE EXTENSION` と一度の `LOAD` をしても、次のセッションでは読み込まれない。毎回 `LOAD` が要る。`LOAD` せずに `dbms_stats.backup_database_stats(...)` などを呼ぶことはできてしまうが、想定外の動作がありうる。
