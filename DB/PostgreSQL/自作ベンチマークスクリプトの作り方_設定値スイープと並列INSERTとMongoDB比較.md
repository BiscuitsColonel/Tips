# 自作ベンチマークスクリプトの作り方: 設定値を総当たりで変える pgbench、並列 INSERT、PostgreSQL と MongoDB の比較

PostgreSQL の設定値（`shared_buffers`・`work_mem`・並列クエリ関連）を変えながら性能を測るシェルスクリプトと、並列 INSERT・PostgreSQL と MongoDB の同一ワークロード比較をする簡易スクリプトの、設計上の工夫のまとめ。`pgbench` のオプションは公式ドキュメントを見る。

（2020-11〜2021-08 時点のメモ。スイープ用スクリプトは PostgreSQL 12 のパス前提。元のメモにはスクリプトだけがあり、測定結果は残っていない）

## 設定値をスイープする pgbench スクリプト（2 本）

1 本目は `shared_buffers` と `work_mem`、2 本目は並列クエリ関連の設定を変える。共通する作りは次のとおり。

- パラメーターの組み合わせを配列に持ち、入れ子の `for` で総当たりする。ログのファイル名にパラメーターの値を埋める（`pgbench_mwp<値>_mpwpg<値>_jcl<値>.log` のように）。後から結果を並べやすい。
- 1 回ごとに、`sed` で `postgresql.conf` の該当行を書き換え、`autovacuum = off` にし、`sync; echo 3 > /proc/sys/vm/drop_caches` で OS のキャッシュを捨てて、`pg_ctl restart` で設定を反映する。測定前の状態を揃えるための 3 点セット。
- 設定を反映したあと `SHOW` で実際の値をログに残す。`sed` の置換が空振りしていないかが、後から分かる。
- 実行は `pgbench -n -c <接続数> -j <スレッド数> ...`。接続数とスレッド数は固定し、変えるのは設定値だけにする。

`shared_buffers` 側は、データ量とバッファの大きさを実メモリに対する割合で表して回す。

```sh
# データ量: 実メモリの 50% / 100% / 200%
PGDATAPER=(50 100 200)
# shared_buffers: pgbench の DB サイズの 50% / 100% / 150%、または実メモリの 10%〜80%
PGSBPER1=(50 100 150)
PGSBPER2=(10 25 40 50 80)

# pgbench のスケール = (狙うDBサイズ - 初期サイズ8MB) / スケール1あたり15MB
SCALE=$(( (TOTALMEM_KB / 1024 * PER / 100 - 8) / 15 ))
```

`work_mem` は、実メモリから `shared_buffers` を引いた残りの一部を割り当て（元のスクリプトでは `(実メモリ - shared_buffers) / 100 / 4`）、64kB を下回る組み合わせは測らずに飛ばす。

2 本目は、`max_worker_processes`（CPU 数の半分と全数）、`max_parallel_workers_per_gather`（0、2、CPU 数の半分、全数）、`join_collapse_limit`（3、5、8）を総当たりする。測定中は `mpstat -P ALL 1`、`vmstat -t 1`、`top -d 1 -b | grep 'load average'` をバックグラウンドで動かして別々のログに落とし、`pgbench` が終わったら PID を指定して止める。測るクエリは SQL ファイルを引数で渡して `pgbench -n -f` で流す。

## 自分で時間を測る簡易ベンチマーク（3 本）

`init` でテスト用のテーブルと SQL ファイルを作り、`run` で測り、`clean` で後片付けをする、の 3 サブコマンドの形にした 3 本のスクリプト。

- 並列 INSERT を測る 2 本。複数テーブルに同時に流すものと、1 つのテーブルに流すもの。後者はテーブルサイズと 1 件あたりの格納サイズも出す。テーブルの型と `USING <テーブルアクセスメソッド>` を引数にでき、`init` で `INSERT` 文のファイルを作る（複数テーブル版はテーブルごとに同じ内容のファイルを複製し、単一テーブル版は総件数を並列数で割った件数のファイルを作る）。
- PostgreSQL と MongoDB に同じワークロードを流して応答時間を比べる 1 本（YCSB を真似たもの）。データは JSON 文字列のカラム 1 つ、PostgreSQL は `val::json::jsonb->'field0'` に B-tree、MongoDB は `field0` にインデックスを張る。ワークロードは Read/Update が 50/50、95/5、Read 100%、Read/Insert が 95/5 の 4 種類。

測り方の工夫は次のとおり。

- `psql` では `\o /dev/null` と `\timing on` を先頭に置いた SQL ファイルを `-f` で流す。出力は捨てて、`Time:` の値だけを `tr -cd '0-9.\n'` で数値に絞る。MongoDB は JavaScript の `new Date()` の差を `print` する。どちらも 1 行 1 値になるので、`awk` で最小・最大・平均が出せる。
- 並列実行は `seq <並列数> | xargs -P <並列数> -I % bash -c "psql ... -f <SQLファイル>"` で起こす。
- 初回のクエリはキャッシュが冷えていて遅い。`-H` オプションで、最初に実行したクエリの時間を結果から除く。指定の有無で、集計に使う範囲（先頭 1 件を含めるかどうか）を `head`・`tail` で切り替える。
- `init` が作る設定ファイル（ホスト、ポート、DB、テーブル名、型）を `run`・`clean` が読む形にして、`run` の引数を減らす。`init` が済んでいないまま `run` すると止まる。
- 比較条件がずれないよう、PostgreSQL と MongoDB のどちらも同じ行数・同じフィールド数・同じサイズ範囲のデータを `init` が生成する。
