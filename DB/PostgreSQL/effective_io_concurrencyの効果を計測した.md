# effective_io_concurrency をビットマップヒープスキャンで試した結果（1 → 0 で 20.9 秒が 3.6 秒）

`effective_io_concurrency` が実際に効く場面と、効かない（逆効果になる）場面を、strace と blktrace で確かめたメモ。

（2021 年のメモ。PostgreSQL 9.6、CentOS 7 で検証。PostgreSQL 10 以降で試した結果は末尾）

## この設定が効く範囲

ビットマップヒープスキャンでヒープページを読むときだけ、`posix_fadvise(POSIX_FADV_WILLNEED)` で先読みを OS に依頼する。他のスキャンには効かない。ビットマップが指すヒープページが互いに離れているほど効く設定で、近いページが連続するなら先読みに意味が無く、むしろ余計な I/O が増える。

## 検証手順

500 万行のテーブルに BRIN インデックスを張り、`id % 2 = 0` という行を絞れない条件を付けて、ビットマップヒープスキャンを強制する。

```sql
CREATE TABLE foobar(id serial PRIMARY KEY, created_at timestamp, data text);
-- created_at は 1 秒ずつ進み、data は 900 バイトの固定文字列。1 ページに約 8 行入る
CREATE INDEX foobar_created_at_brin ON foobar USING brin(created_at);

SET effective_io_concurrency = 1;
EXPLAIN ANALYZE SELECT COUNT(*) FROM foobar
 WHERE created_at > '2019-02-01' AND id % 2 = 0;
```

## 結果

| effective_io_concurrency | 実行時間 |
| --- | --- |
| 1 | 約 20.9 秒 |
| 0 | 約 3.6 秒 |

`Heap Blocks: lossy=290280`（BRIN なのでページ単位）、`Rows Removed by Filter` が 116 万行。行を絞れず、実質ほぼ全ページを順に読む処理になっていた。

`strace` では、先読みの `fadvise64(..., 8192, POSIX_FADV_WILLNEED)` が 8KB ずつ連続した領域に対して大量に発行されていた。`blktrace` では、1 だと 8KB のリードが連続して発行され、0 だと 512KB 単位のリードにまとまった。OS のシーケンシャルリード最適化で抑えられるはずの I/O 発行回数が、先読み指定によって数倍から数十倍に膨らんでいた。

## 学んだこと

- 隣接するページを順に読むような、シーケンシャルに近いビットマップスキャンでは、先読み指定で I/O の発行回数が増え、逆に遅くなりうる。
- 今回のテストは BRIN でデータを隣接させた極端な例なので、実運用でここまで差が出るとは限らない。無効化は効果を試す価値があるが、特定のクエリだけ `SET` でオフにして比べる方法もある。
- PostgreSQL 10 以降で試したところ、パラレルビットマップスキャンでは 1 にしても `read_ahead` が機能していた。パラレルでない場合は 9.6 と同じ挙動になる。
