# NLB 配下の HAProxy 冗長化（Pacemaker）を障害種別ごとに落として確認した結果と、切り替え時間の見積もり

NLB -> HAProxy（Pacemaker の Active/Standby）-> バックエンドの構成で、プロセス停止・OS ハング・バックエンド停止を 1 つずつ起こして切り替わり方を確かめた記録。構成と設定値は [HAProxyをPacemaker2台で冗長化しバックエンドを手動切り戻しにする設計.md](HAProxyをPacemaker2台で冗長化しバックエンドを手動切り戻しにする設計.md) にある。

（2021-10 時点のメモ。Amazon Linux 2、Pacemaker 1.1.23。HAProxy 3 台、バックエンド 3 台、各 AZ に 1 台ずつで検証。）

## 試験の作り方

バックエンドはアプリを入れず、`nc` で「自分の名前を返すだけ」のサーバにした。どのバックエンドに届いたかが `curl` の応答で分かる。

```sh
bash -c 'trap exit INT; while true; do ( echo "HTTP/1.0 200 Ok"; echo; echo "BACKEND1" ) | nc -l 8080; done'
```

クライアントからは NLB に対して `while true; do curl http://<nlb-dns>:8080; sleep 0.1; done` を流し続け、止まった時刻と切り替わった時刻を見る。切り替わる様子は Standby 側で `crm_mon` を出しておくと追える。

## 結果

| 起こした障害 | 起こし方 | 結果 |
| --- | --- | --- |
| Pacemaker の停止 | `kill -9 pacemakerd` のあと `systemctl stop pacemaker` | kill だけだと systemd が再起動するので、停止まで必要。切り替わり、CloudWatch のアラートも出た |
| Corosync の停止 | `kill -9 corosync` | 切り替わる。タイミングによっては元の Primary が Primary を保持することがあるが、悪影響はない。Corosync が落ちると Pacemaker も落ちる場合があり、アラートは両方出ることがある |
| HAProxy の停止 | `kill -9 haproxy` を 2 回 | 1 回目は Pacemaker が起動し直すだけ。`migration-threshold=2` なので 2 回目で切り替わる |
| OS のハング | `echo c > /proc/sysrq-trigger` | `kernel.panic=5` で再起動し 20 秒ほどで復帰したため、切り替わらず元の Primary が続けた。`token` が 30 秒なので、それより早く戻れば切り替えは起きないと考えられる |
| バックエンドのポート停止 | バックエンド1の `nc` を停止 | 約 10 秒後に予備へ切り替わり、アラートも出た |
| バックエンドの復旧 | `nc` を再起動 | 自動では戻らない。`socat` で `disable` -> `enable` したときだけ戻る |

2 台目の障害を起こす前に、3 台目の Pacemaker を起動してクラスタに参加させてから続けた（`systemctl start pacemaker`、参加は `crm_mon` で確認）。

メインのポートだけを落としたとき、同じバックエンドを向く別ポートはしばらく生きたバックエンドに送り続け、ポートごとのヘルスチェックで落ちたと分かった時点で予備へ移った。ポートごとに切り替えタイミングがずれる。

HAProxy 停止後の Primary 側で、HAProxy が動いているかを 1 行で確認するのにこの式を使った（0 が返れば正常）。

```sh
echo $(( $(pcs status | grep haproxyd.*Started | echo $?) + $(ps -ef | grep haproxy | grep -v grep | echo $?) ))
```

## 切り替わりに実際にかかる時間

プロセス障害の場合、Pacemaker 側の切り替えは 1 秒ほどで終わるが、NLB がそれを認識するまでが長い。

| 区間 | 時間 |
| --- | --- |
| Pacemaker が Active を切り替える | 1 秒 |
| NLB のヘルスチェックが完了する（最短の 10 秒間隔 x 2 回） | 20 秒 |
| ヘルスチェックが通ったターゲットへ接続が割り当たる | 0 〜 30 秒 |
| 合計 | 21 〜 51 秒 |

OS ごと落ちる場合は、再起動を待って切り替わるまでが加わり 80 〜 110 秒を見込んだ。`kernel.panic` を 30 秒から 5 秒に変えると、ここが 25 秒縮む見込み（設定値の差からの計算で、30 秒設定での試験はしていない）。

さらに縮めたいなら、ヘルスチェックの間隔と回数を減らす（NLB の最短が 10 秒 x 2 回なので限界がある）、または NLB をやめて EIP を VIP のように付け替える方式にする。

### 切り替え直後のすれ違い

切り替え直後の約 20 秒は、NLB から見て旧 Active（もう HAProxy が止まっている側）がまだ healthy のことがあり、新 Active と旧 Active の両方に振り分けられる。旧側は HAProxy が落ちているので、その間のリクエストは失敗する。切り替え中の一時的な失敗として許容した。

## AZ をまたぐバックエンドの遅延

HAProxy と別 AZ のバックエンドへつないでも動作に問題はなく、遅延は 3 ms 前後増えるだけだった（同 AZ で 0.0067 秒、別 AZ で 0.0103 秒の応答時間）。NLB は HAProxy にしか振り分けないので、バックエンドの AZ 配置を意識する必要はない。
