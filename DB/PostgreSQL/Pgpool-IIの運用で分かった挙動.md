# Pgpool-II の運用で分かった、マニュアルだけでは気づきにくい挙動

PostgreSQL の前段に置く Pgpool-II と、管理画面 pgpoolAdmin について、サポート問い合わせで分かった挙動をまとめたメモ。

（2020〜2021 年ごろのサポート問い合わせの記録。Pgpool-II 3.7〜4.2、PostgreSQL 10〜13）

## ログの意味

- `unable to read data from frontend` / `socket read failed with an error "Connection timed out"`: クライアントからの読み込みに失敗しただけで、Pgpool-II のサービスには影響しない。クライアントが応答しなかった場合（ネットワーク障害、ポートスキャンによるパケット遮断、OS 障害）に出る。`Connection reset by peer` はクライアント側から RST が返った場合で、コネクションの閉じ忘れなどで OS が通信を切ったとき。頻発するならネットワーク機器の設定変更の時期とクライアントの操作を突き合わせる。
- `unable to read data from DB node 0 / EOF encountered with backend`: バックエンドとの接続が切れた。同じ時刻に PostgreSQL 側で `using stale statistics instead of current ones because stats collector is not responding` が出ていたら、DB サーバーが高負荷で、ヘルスチェックに応答できなかった可能性が高い。ストレージのコントローラが再起動して I/O 待ちになっていた場合でも同じログが出うる。

## `pg_terminate_backend()` でフェイルオーバーする

Pgpool-II を経由して `pg_terminate_backend` を実行すると、引数が定数（単純な整数）でない場合にフェイルオーバーが起きる。`pg_stat_activity` の結果をそのまま引数にした一括 kill は避け、pid を確認して定数として埋め込んだ文を、pid の数だけ実行する。

## pgpoolAdmin

- pgpoolAdmin から起動した pgpool は、httpd のユーザー（apache）で動き、pid ファイルも apache 所有になる。postgres ユーザーで動かすなら apache の suEXEC を使うことになるが、セキュリティ上の注意が要る。
- バックエンドの状態が「ダウン」と出るのに実際は生きているときは、`pgpool.conf` の `health_check_database` が未指定だと疑う。Pgpool-II 本体は未指定なら `postgres` と `template1` を見るが、pgpoolAdmin は挙動が違い、正しく接続できない（この差はコミュニティに報告された）。`postgres` などを明示する。
- 「リカバリ」ボタンのオンラインリカバリが `recovery request is only allowed in replication and streaming replication modes` で失敗するのは、マスタースレーブモードで動いているため。マニュアルには「いずれのモードでもオンラインリカバリを提供する」とあるが、実際は違う（これもコミュニティに報告された）。マスタースレーブモードでは、手動で PostgreSQL を復旧してから「復帰」を実行する。ただしサブモードがストリーミングレプリケーション（`master_slave_sub_mode = stream`）なら「リカバリ」も使える。
- リカバリは対象の `template1` に接続して行うので、ヘルスチェックが失敗していても影響しない。

## 設定値

- `wd_priority`: 大きい方が優先。ただし 2 ノードを同時に起動したときだけ効く。起動に間隔がある場合や、同じ値の場合は、先に起動した方が active になる。この設定は 3.5 から（[公式ドキュメント](https://www.pgpool.net/docs/latest/en/html/runtime-watchdog-config.html)に「V3.5 より前では使えない」とある）。3.5 より前は、差を付けなかった場合と同じ動き。
- `failover_when_quorum_exists`: 2 ノード構成では on でも off でも挙動は変わらない。差が出るのは 3 ノード以上のときで、on なら Pgpool-II ノードの過半数が障害と判断したときだけフェイルオーバーする。
- `memqcache_cache_block_size` と `memqcache_maxcache` は、省略したときのデフォルト（1048576 と 409600）が環境によらず固定。マニュアルには値の記載が無い。キャッシュ領域はブロック単位で管理され、足りなくなるとおおむね登録の古い順に消して再利用する。`memqcache_method = shmem` のときは `memqcache_maxcache` が `memqcache_cache_block_size` を超えない値にする必要がある。カーネルの `kernel.shmmax` については、「1 プロセスの上限」というサポートの説明と、「領域ごとの制限で、全体の上限は `shmall`」という指摘があり、どちらが正しいかは未確認。
- `log_rotation_size = 0` は 4.2.1 で `0 is outside the valid range` の FATAL になって起動しない（実装バグかドキュメントの不備として報告された）。サイズによるローテーションを実質無効にするには最大値 `2147483647` を指定する。
- `app_name_redirect_preference_list` で振り分け先に指定できるのは `primary`、`standby`、ノード番号だけで、同期と非同期を区別できない。同期スタンバイと非同期スタンバイを分けたいなら、ノード番号とその役割を固定する。同期群と非同期群を別々の Pgpool-II で管理する構成も可能だが、非同期側は相手の状態を知らないので、レプリケーション元の障害時に元を付け替える仕組みを自前で用意することになり、`delay_threshold` による遅延ノードの除外も効かない。

## フェイルオーバーまわり

- `failover_command` のスクリプトを書き換えただけなら、Pgpool-II の再起動も reload も要らない。パラメータを変えたときだけ要る。
- Pgpool-II 自体の障害（マスター／スタンバイの入れ替え）には、カスタムスクリプトは要らない。watchdog が `ip` と `arping` で行う。入れ替えを契機に処理を呼びたいときは、`wd_escalation_command`（昇格時）と `wd_de_escalation_command`（降格時）に指定する。
- `online_recovery` の後でスレーブを起動すると、マスター側の書き込みも止まった例があった。同期スタンバイの設定のため、ダウン中の更新が追い付くまでマスター側のコミットが待たされるのが原因とみられる（その後の結果は未確認）。
- 切り離した旧マスターを新スタンバイとして戻す手順（同期が取れていればオンラインリカバリは不要）:
  1. 新マスターにレプリケーションスロットを作る
  2. 新スタンバイに `recovery.conf` を作る
  3. `pg_rewind` で新マスターの内容に同期する
  4. 新スタンバイを起動する
  5. スロットの状態で遅れが小さくなるまで待つ
  6. 新マスターの `synchronous_standby_names` を空にして reload（一時的に非同期にする）
  7. 新スタンバイを Pgpool-II に attach する

## PostgreSQL 13 との組み合わせ

Pgpool-II 4.1.x で PostgreSQL 13 を扱うなら、4.1.5 を使う。PostgreSQL 13 向けの rpm はこのバージョンから提供されている。対応バージョンはドキュメントに明記されていないので、判断の目安は rpm の有無になる。4.1.4 以前でもソースからのビルドで操作はできるが、サンプルの `failover.sh` と `follow_master.sh` がそのまま動くかは要確認で、Pgpool-II 本体の修正が要るかもしれない。
