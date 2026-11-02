# PostgreSQL の性能・運用に効く Linux カーネル設定と postgresql.conf の値の選び方

PostgreSQL サーバー構築時に、デフォルトのままにしないほうがよい設定を、「なぜその値か」とセットにまとめたメモ。パラメーターの意味は [公式ドキュメント](https://www.postgresql.org/docs/current/runtime-config.html) を見る。

（2021-06 時点のメモ。元メモに対象バージョンの記載は無く、`jit` や `max_parallel_maintenance_workers` を含むので PostgreSQL 11 以降向き）

## Linux カーネル

- ダーティページ: 共有バッファが足りなくなったとき、捨てるページがダーティだと先にディスクへ書く必要があり、応答が遅くなる。更新が多いとチェックポイントで書き出すページも増え、その間の処理能力が落ち込む。OS 側のライトバックを早めに始めるため、`vm.dirty_background_ratio`（デフォルト 10）を 5、`vm.dirty_ratio`（デフォルト 40）を 20、`vm.dirty_writeback_centisecs`（デフォルト 500）を 250 に下げる。`vm.zone_reclaim_mode` は 0（NUMA でキャッシュが捨てられるのを防ぐ）。
- HugePage: `shared_buffers` が大きいときのオーバーヘッドを減らす。必要数は、起動中の postmaster の PID（`head -1 $PGDATA/postmaster.pid`）から `grep ^VmPeak /proc/<PID>/status` を読み、`Hugepagesize`（`/proc/meminfo`）で割って切り上げる。例: VmPeak 5565496 kB ÷ 2048 kB = 2717.5 → 2718。`vm.nr_hugepages` に設定して `/etc/sysctl.conf` に永続化し、`postgresql.conf` で `huge_pages = on`。
- メモリオーバーコミット: `vm.overcommit_memory = 2` にすると OOM killer の発生頻度をかなり下げられる（ゼロにはならない）。1 にすると OOM killer が起きやすいが性能は出る。

## postgresql.conf

| 設定 | 目安と理由 |
| --- | --- |
| `shared_buffers` | 物理メモリの 4 分の 1 程度。DB がメモリに載り切るならそれと同じ大きさ。50% を超えるとカーネルのキャッシュが溢れてスワップする |
| `work_mem` | 最初は 32MB 程度から始めて、`log_temp_files` のログを見ながら倍々に増やす。実行計画の sort に `Disk` と出ていたら足りない。上限の目安は (物理メモリ − `shared_buffers`) ÷ `max_connections` |
| `log_temp_files` | 0 にする。メモリに載り切らなかった一時ファイルを全部知りたい（1MB などで切ると、あと少しで載り切らなかったものを取りこぼす） |
| `max_wal_size` / `checkpoint_timeout` | ログに `checkpoints are occurring too frequently` が出たら `max_wal_size` を増やす。`checkpoint_timeout` は長くするほど書き込み頻度が減る（リカバリ時間とのトレードオフ） |
| `checkpoint_completion_target` | (`checkpoint_timeout` − 2 分) ÷ `checkpoint_timeout` を目安に、書き出しを分散させる |
| `autovacuum_vacuum_scale_factor` | 行数の多いテーブルは小さくする。ただし `postgresql.conf` に書くと全テーブルに効くので、`ALTER TABLE ... SET (...)` でテーブル単位に設定する |
| `autovacuum_work_mem` | 自動 VACUUM のログ（`log_autovacuum_min_duration`）で `index scans` が 2 以上なら、メモリを増やすと効く |
| `autovacuum_max_workers` | 大きなテーブル（DB サイズの 20% 超）の数 + 1 |
| `random_page_cost` | デフォルト 4。SSD は 1.1、高 IOPS の RAID は 2.0〜3.0。小さくするとシーケンシャルスキャンよりインデックススキャンが選ばれやすくなる |
| `effective_io_concurrency` | ディスクドライブの数が目安（RAID 10 で 4）。SSD / NVMe は 128。ただし効くのはビットマップヒープスキャンのみで、逆効果になる場合もある |
| `default_statistics_target` | `LIKE` 検索がある列は 100 が目安。大きくするほど推定が細かくなり、ANALYZE が遅くなる。テーブル・列単位は `ALTER TABLE ... SET STATISTICS` |
| `synchronous_commit` | `off` にするとコミットが速くなるが、クラッシュで直近のコミットを失いうる。全体では変えず、性能計測して意味のある処理だけ `SET LOCAL synchronous_commit TO OFF` にする |
| `deadlock_timeout` | 元メモの値は「デフォルト 1 秒 × 同時セッション数」。根拠は未確認なので、そのまま採用しない |
| `tcp_keepalives_idle` / `interval` / `count` | アプリが落ちた、ネットワークが切れたなどで、DB 側にプロセスが残り接続数が上限に達する／ロングトランザクションになるのを防ぐ。60 / 5 / 6 で約 1 分半で除去できる（デフォルトは 7200 / 75 / 9） |
| `lc_messages` | `en_US` にしておくと文字化けしない |
| `join_collapse_limit` / `from_collapse_limit` / `geqo` | テーブルを多く結合するクエリで、計画作成時間がボトルネックになるときは閾値を下げる |
| `dynamic_shared_memory_type` | パラレルクエリに必要 |

パラメーターのうちいくつかは、ユーザーや DB 単位でも設定できる。

```sql
ALTER USER some_user SET log_statement TO 'all';
ALTER DATABASE some_db SET statement_timeout TO '60s';
```

`SET LOCAL` はそのトランザクションの間だけ有効。`work_mem` を大きくしたい重い処理だけ、`BEGIN; SET LOCAL work_mem TO '128MB'; ...` のように使う。

## レプリケーション

- `max_standby_streaming_delay`（アーカイブ経由は `max_standby_archive_delay`）: スタンバイの問い合わせが WAL 適用と競合したとき、何秒まで適用を待つか。遅延が積み重なるのを防ぐための上限
- `hot_standby_feedback`: スタンバイのクエリが中断されすぎるときに `on`。プライマリで行の削除が遅れて肥大する可能性がある
- `synchronous_standby_names`: 同期レプリケーションの対象。空だと非同期
- `synchronous_commit` の段階: `remote_apply`（スタンバイで参照可能になるまで待つ）、`on`（スタンバイで WAL を書き込むまで）、`remote_write`（スタンバイが受け取るまで）、`local`（プライマリの WAL 書き込みまで）、`off`（待たない）

## 設定値をサーバーの実測値から算出して突き合わせる自作スクリプト

（2021-02 時点に書いた自作の Python スクリプト `pg_setchk` のメモ。Linux 専用で、`root` で実行する前提。PostgreSQL のバージョンは `max_parallel_maintenance_workers` を扱うので 11 以降向き）

上の表の目安を、搭載メモリ・CPU・ディスク種別から数値に落とし、`pg_settings` と `sysctl -a` の現在値と比べて外れているものだけ指摘する。`-m test` は指摘だけ、`-m config` は設定ファイルに貼れる `name=value` を出力、`-m devel` は開発環境向けのログ設定なども足す。`-n` で、同じサーバーに載せるインスタンス数を指定し、メモリと CPU をその数で割る。値は「推奨値 ± 許容幅」で判定し、幅に入っていれば指摘しない。

| 設定 | スクリプトの算出式 | 許容幅 |
| --- | --- | --- |
| `shared_buffers` | メモリ ÷ 4 | ±10% |
| `work_mem` | (メモリ − `shared_buffers`) ÷ `max_connections` ÷ 3 | ±10% |
| `maintenance_work_mem` | メモリ × 10% | ±10% |
| `effective_cache_size` | メモリ ÷ 2 | ±10% |
| `max_parallel_workers` / `max_worker_processes` / `max_parallel_workers_per_gather` | CPU コア数 × 0.8 | ±CPU × 0.2 |
| `max_parallel_maintenance_workers` | 上の半分 | 半分 |
| `checkpoint_timeout` | 1800 秒 | 1800〜3600 秒 |
| `checkpoint_completion_target` | (1800 − 120) ÷ 1800 = 0.93 | ±0.09 |
| `tcp_keepalives_idle` / `interval` / `count` | 120 / 30 / 4（合計 240 秒） | 合計の ±25% |
| `deadlock_timeout` | `max_connections` × 1000 ms（元メモの式。根拠は未確認） | なし |
| `autovacuum_max_workers` | `relpages >= 128000` のリレーション数 + 1 | ±2 |
| `default_statistics_target` | 2000 | ±500（ANALYZE に時間がかかる旨の警告つき） |
| `random_page_cost` | SSD 1.1、HDD 2.5 | なし |
| `effective_io_concurrency` | SSD 200、HDD は `/proc/mdstat` の RAID メンバー数（なければ 1） | なし |
| `max_wal_size` / `min_wal_size` | 10240MB、両者を同じ値に | なし |
| `max_stack_depth` | `ulimit -s` − 1024 kB | なし |
| `archive_mode` | `on`（`archive_command` の例も出す） | なし |

Linux 側は `vm.nr_hugepages`（起動中の postmaster の `VmPeak` ÷ `Hugepagesize`）、THP の `defrag` が `never` か、`kernel.shmmax`（`shared_buffers` 以上）、`vm.overcommit_memory = 2`、`vm.dirty_background_ratio` 5、`vm.dirty_ratio` 20、`vm.dirty_writeback_centisecs` 250、`vm.zone_reclaim_mode` 0 を同様に比べる。

この表と上の目安で値が食い違う項目は、スクリプトを書いた時点と上のメモを書いた時点で考えが変わったと読める（確認はできていない）。`tcp_keepalives_*` は上が 60 / 5 / 6、スクリプトは 120 / 30 / 4。`effective_io_concurrency` は上が NVMe 128、スクリプトは SSD 200。`default_statistics_target` は上が 100（`LIKE` 検索がある列）、スクリプトは 2000。`deadlock_timeout` も、上の表は「1 秒 × 同時セッション数」、スクリプトは `max_connections` × 1000 ms と、同じ式でも掛ける数が違う。`autovacuum_max_workers` は上が「DB サイズの 20% 超のテーブル数 + 1」、スクリプトは「`relpages` 128000 以上（8KB ページで約 1GB）のリレーション数 + 1」。どちらを使うかは環境で決め直すこと。

スクリプトの `kernel.shmmni` は `(max_connections + autovacuum_max_workers + 4) ÷ 16` で算出している。この形の式は SysV セマフォの数（`SEMMNI`）に当てるもので、現行の公式ドキュメントは `SEMMNI` を `postgres -C num_os_semaphores` の値から `ceil(num_os_semaphores / 16)` で求めると書き、`SHMMNI` に算出式は示していない。`shmmni` に当てているのは取り違えの疑いがある。ヒュージページ数も、現行の公式ドキュメントは `postgres -C shared_memory_size_in_huge_pages` で求める方法を載せている（上の `VmPeak` を使う方法とは別の手段）。出典: https://www.postgresql.org/docs/current/kernel-resources.html
