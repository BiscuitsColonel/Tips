# HAProxy を Pacemaker で冗長化し、バックエンドは自動で切り戻さない構成の設計と設定値の理由

AWS 上で NLB の配下に HAProxy を 2 台置き、HAProxy を Pacemaker/Corosync で Active/Standby にしたうえで、HAProxy の先の 2 台のバックエンドも「障害時は予備へ切り替わり、復旧しても自動では戻らない」構成にしたときの判断と設定値の理由。

（2021-10〜11 時点のメモ。Amazon Linux 2、Pacemaker 1.1.23 で検証。TCP 負荷分散で、バックエンドは同時に 1 台しか受けない前提。）

## 構成

```text
クライアント -> NLB -> HAProxy (Pacemaker で Active/Standby) -> バックエンド1 (通常) / バックエンド2 (予備)
```

- バックエンドは同時に 1 台しか受けられない構成で、復旧したバックエンドへ勝手に戻ると 2 台が同時に受けてしまう。そのためバックエンドの切り替えは HAProxy 側で「障害時のみ予備へ、復旧しても戻さない」にした
- NLB は Standby 側の HAProxy にもヘルスチェックを打つが、Standby は HAProxy を起動していないので失敗して振り分け対象から外れる。Pacemaker が HAProxy を起動した側だけが NLB の healthy になる
- 共有ストレージを持たないクラスタなので STONITH は使わない。Watchdog は Corosync 側のものを使うので Pacemaker 側では使わない
- EC2 ではマルチキャストが使えないため、Corosync は `transport: udpu` にする（検討時、Keepalived もマルチキャストの制約で組めない可能性が高いと見ていた）

## 設定値と理由

### OS

| 項目 | 初期値 | 設定値 | 理由 |
| --- | --- | --- | --- |
| `kernel.panic` | 30 | 5 | パニック後の再起動を早め、切り替わりまでの時間を 25 秒縮める見込み（`kernel.panic` の値の差から計算した値で、30 秒設定との比較は試験していない） |
| `kernel.panic_on_oops` | 0 | 1 | oops を放置せずパニックさせて再起動に倒す |

### Pacemaker / Corosync の起動停止まわり

| 対象 | 設定 | 理由 |
| --- | --- | --- |
| `/etc/sysconfig/pacemaker` | `PCMK_fail_fast=yes` | Pacemaker 内部プロセスの故障もノード故障として扱う |
| `corosync.service` | `Restart=on-failure` と `RestartSec=70` | 異常終了時に再起動する。再起動は終了から 70 秒後 |
| `corosync.service` | `ExecStartPre=/sbin/modprobe softdog soft_margin=6` | Corosync の故障を 6 秒以内に検知させる |
| `pacemaker.service` | `ExecStopPost=/bin/sh -c 'pidof crmd \|\| killall -TERM corosync'` | Pacemaker が止まったら Corosync も一緒に止め、中途半端にクラスタに居残らせない |

### corosync.conf

| 項目 | 設定値 | 理由 |
| --- | --- | --- |
| `transport` | `udpu` | マルチキャストを使わない |
| `token` | 30000 ms | 一時的な遅延で切り替わらないよう、既定の 1000 ms から長くした |
| `join` | 1500 ms | `token` に合わせて長めにする |
| `quorum.two_node` | 1 | 運用は 2 ノードが基本。設定上は 3 ノード分を書いても `two_node: 1` にした |

3 ノード目を足した構成で `pcs status` に `partition WITHOUT quorum` と出ても、`no-quorum-policy=ignore` なら動き続ける。表示だけで慌てない。

### Pacemaker のプロパティとリソース

| 項目 | 設定値 | 理由 |
| --- | --- | --- |
| `no-quorum-policy` | `ignore` | 2 ノードではクォーラムを使わない |
| `stonith-enabled` | `false` | 共有ストレージが無い |
| `have-watchdog` | `false` | 不安定なノードを自動で再起動しない |
| `pe-*-series-max` | 0 | スケジューラの計算結果ファイルを残さない |
| `migration-threshold` | 2 | 2 回失敗したら別ノードへ |
| `failure-timeout` | 60s | フェイルカウントを 60 秒で自動クリアする |
| `cluster-recheck-interval` | 60s | `failure-timeout` に揃える。既定の 15 分のままだとカウントのクリアが最大 15 分遅れる |
| `resource-stickiness` | INFINITY | フェイルバックしない |
| monitor `interval` | 1s | HAProxy の死活を 1 秒で見る |

リソースは HAProxy だけ。HAProxy の OCF スクリプトは公開されているもの（<https://github.com/russki/cluster-agents>）を使い、監視はプロセスの有無と設定ファイルの有無にした。

### HAProxy

```text
global
    log 127.0.0.1 local2 info
    stats socket /tmp/haproxy-cli.sock user root group wheel level admin

defaults
    mode tcp
    option tcplog
    balance roundrobin
    retries 1
    timeout connect 60s
    timeout client  60s
    timeout server  60s

backend tcp-servers
    server backend1 192.0.2.10 weight 1 inter 1s rise 1215752191 fall 10 check port 8080
    server backend2 192.0.2.20 backup inter 1s rise 10 fall 10 check port 8080
```

- `rise 1215752191` が肝。ヘルスチェックが何回成功すれば復活とみなすかの回数を極端に大きくして、バックエンド1が復旧しても事実上自動では戻らないようにしている。`show stat` では `DOWN 1812/1215752191` のように表示される
- `backup` を付けたバックエンド2は、バックエンド1が `fall 10`（1 秒間隔で 10 回失敗）で落ちたときだけ使われる
- `stats socket` を `level admin` で開けておくと、`socat` で手動操作できる

## 手動で切り戻す・足す

バックエンド1を戻すとき。復旧させてもまだ DOWN のままなので、いったん `disable` してから `enable` するとカウンタが戻り、UP になって元の向き先に戻る。

```sh
echo "disable server tcp-servers/backend1" | socat stdio /tmp/haproxy-cli.sock
echo "enable server tcp-servers/backend1"  | socat stdio /tmp/haproxy-cli.sock
echo "show stat -1 4 -1" | socat stdio /tmp/haproxy-cli.sock | grep -v -E '^#|^$' | cut -d, -f2,18
```

`disable` するとログに `was DOWN and now enters maintenance.` と出る。障害時の `Server ... is DOWN, reason: Layer4 connection problem` とは別の文言なので、ログ監視のキーワードを作るときは区別する。

向き先を増やす・外すときは、設定ファイルに `server` 行を足して（または `sed -i` で消して）から、接続を切らずに再読み込みする。Active と Standby の両方の設定ファイルを同じように直しておくこと。

```sh
haproxy -f /etc/haproxy/haproxy.cfg -p /var/run/haproxy.pid -sf $(cat /var/run/haproxy.pid)
```

`curl` を 0.1 秒間隔でループさせたまま足し引きして、エラーなく継続することを確認した（追加も削除もダウンタイムなし）。

## ログ監視のキーワード

| 事象 | 出力元 | キーワード |
| --- | --- | --- |
| Pacemaker 自体が停止 | `/var/log/messages`（systemd） | `pacemaker.service failed` |
| ノードと疎通できない | Corosync / Pacemaker | `Node <name> state is now lost` |
| HAProxy が停止 | `/var/log/messages`（OCF スクリプト） | `haproxy daemon is not running` |
| バックエンドが停止 | HAProxy | `Connection refused` |

ログは EC2 内でローテートせず、CloudWatch Logs に送って保存と監視をまとめる方針にした。

試験の結果とダウンタイムの見積もりは [NLB配下のHAProxy冗長化のフェイルオーバー試験とダウンタイム見積もり.md](NLB配下のHAProxy冗長化のフェイルオーバー試験とダウンタイム見積もり.md)。
