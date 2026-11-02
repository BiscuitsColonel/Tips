# PostgreSQL のレプリケーションで WAL が足りなくなる・同期が切れる・切り替えで迷うときの挙動メモ

ストリーミングレプリケーションと論理レプリケーションの運用で、サポートに問い合わせて分かったことをまとめたメモ。切り分けの手がかりになるログと、切り替え時に迷う点が中心。

（2020〜2021 年ごろのサポート問い合わせの記録。PostgreSQL 10〜12。`wal_keep_segments` は 13 で `wal_keep_size` に変わっている）

## VACUUM の最中にレプリケーションが外れる

- 現象・条件: 大きなテーブルの VACUUM 中に、スタンバイが必要とする WAL がプライマリから消えてレプリケーションが外れた。
- 分かったこと: VACUUM 自体が大量の WAL を出す。スタンバイへの転送かスタンバイでの適用が遅れるほど、未転送の WAL が消される危険が増える。ネットワーク帯域とスタンバイの負荷が引き金になる。
- 対処:
  - `wal_keep_segments` を VACUUM で出る WAL 量より大きくする。ディスク消費の目安は `(wal_keep_segments + 1) × 16MB`。
  - WAL アーカイブかレプリケーションスロットを併用する。
  - `vacuum_cost_delay` を上げ `vacuum_cost_limit` を下げて、時間あたりの WAL 量を減らす（VACUUM は遅くなる）。
- 同期レプリケーションで外れると、スタンバイから応答が返らずプライマリの更新が止まる。PostgreSQL 自体にはフェイルオーバーする機能が無いので、勝手に切り替わることはない。

## スタンバイが必要とする WAL がいつ消えるか

- 条件: アーカイブ無しで、プライマリとスタンバイの通信が途切れたまま運用を続けた。
- 分かったこと: WAL はチェックポイントを過ぎるといつ消えてもおかしくない。チェックポイントは `checkpoint_timeout` の経過か `max_wal_size` 分の WAL 書き込みで起きるので、消えるまでの時間は更新量で決まる。サポートの見積もり方は、WAL ディレクトリを定期的に見て、最も古い WAL が時間あたりいくつ進むかを測る方法。
- 消えるとレプリケーションは続けられず、ベースバックアップからの作り直しになる。レプリケーションスロットを使うと消えなくなる代わりに、通信が戻らないままだとプライマリの WAL が溢れる。

## レプリケーション異常のときに出るログ

| 側 | メッセージ | 意味 |
| --- | --- | --- |
| プライマリ | `requested WAL segment ... has already been removed` | スタンバイが要求した WAL が既に無い |
| プライマリ | `unexpected EOF on standby connection` | スタンバイとの接続が切れた |
| プライマリ | `terminating walsender process due to replication timeout` | 設定時間を超えて通信できなかった |
| スタンバイ | `could not connect to the primary server` | プライマリに接続できない |
| スタンバイ | `replication terminated by primary server` | プライマリ側から切断された |
| スタンバイ | `terminating walreceiver due to timeout` | 設定時間を超えて通信できなかった |

論理レプリケーションの購読側では `could not connect to the publisher` になる。「異常を表す決まった文字列」は無いので、監視はこれらを拾うのに加えて、プライマリで `pg_stat_replication` の `replay_lsn` と `pg_current_wal_lsn()` を比べる。行が無ければ動いていない。`replay_lag` や `flush_lag` が NULL なら遅れは無い。

## 昇格に成功したかの確認

`pg_ctl promote` に成功確認用のコマンドは無い。次の 2 点で判断する。

- データディレクトリの `recovery.conf` が `recovery.done` になっている（12 より前）
- `SHOW transaction_read_only;` が `off`

`pg_ctl promote` 自体は、成功時は `server promoted`、スタンバイでないときは `cannot promote server; server is not in standby mode`、時間内に終わらなければ `server did not promote in time` を返す。昇格後の再起動は要らない。

## 同期スタンバイの `application_name` に他ノードの名前を入れると同期が引き継がれる

- 現象・条件: プライマリの `synchronous_standby_names = 'FIRST 1 (node2, node3)'` で運用中。node3 の接続設定の `application_name` を自分（node3）ではなく node2 にしておくと、プライマリ停止後に node2 が新プライマリになったとき、node3 が同期スタンバイとして引き継がれる動きをした。
- 分かったこと: `application_name` は自分のサーバー名にするのが正しい。他ノードの名前を入れるのは想定外の挙動を起こしうる、というのがサポートの回答。動くからといって使わない。

## ストリーミングと論理レプリケーションの混在

混在構成は対応範囲。プライマリ障害で購読側を新プライマリへ向け直す手順は次の順で、これで問題ない。

```sql
ALTER SUBSCRIPTION sub DISABLE;
ALTER SUBSCRIPTION sub SET (slot_name = NONE);
DROP SUBSCRIPTION sub;
CREATE SUBSCRIPTION sub CONNECTION '...' PUBLICATION pub WITH (copy_data = false);
```
## 論理レプリケーションの向き先を変えるときの落とし穴

- `copy_data = true` で再作成すると、差分ではなく全行をコピーしようとする。購読側にデータが残っていて主キーが衝突すると、競合でレプリケーションが止まる。
- 初期コピーの最中に購読側のテーブルを SELECT すると 0 件に見える。同期中の参照を拒否する機能は無いので、クライアント側で制御するか、`REVOKE`、`pg_hba.conf`、ロードバランサーで接続を止める。
- プロキシ製品（Pgpool-II 等）にも、論理レプリケーションの切り替え完了を待って処理を受ける機能は無い。

## 復旧に失敗するバックアップの例（wal_level が minimal）

- 現象: 物理コピー＋アーカイブ WAL でリストアしたら、`WAL was generated with wal_level=minimal, data may be missing` の警告の後、`hot standby is not possible because wal_level was not set to "replica" or higher` で起動が止まった。
- 分かったこと: minimal で作られた WAL を再生しようとしているのが原因で、`postgresql.conf` をいくら直しても通らない。バックアップの取り直しが要る。元の設定は `logical` だった。
- サポート側の調査では、リストア先で事前に `pg_resetwal` を実行しており、それでコントロールファイルが minimal 扱いになったと推定された。`pg_resetwal` は不要な手順なので外して再実施する方向になった（その後の結果は記録に無い）。

関連して、`wal_level = minimal` にして再起動するときは `max_wal_senders = 0` も同時に要る。`archive_mode` も minimal では有効にできない（[公式ドキュメント 19.5](https://www.postgresql.org/docs/12/runtime-config-wal.html)）。

## アーカイブ先に WAL が同時刻に大量に並ぶ

原因の候補は、VACUUM FULL のように WAL を大量に出す処理があった場合と、アーカイブ先が満杯でコマンドが失敗し続けていたのが解消して溜まっていた分が一気にコピーされた場合。1 ファイルだけなら `archive_timeout` による強制切り替えを疑う。

## NAT をまたぐレプリケーション

レプリケーションは WAL を TCP/IP で転送するだけなので、拠点間で双方向に TCP が通れば、途中に NAT があっても組める。
