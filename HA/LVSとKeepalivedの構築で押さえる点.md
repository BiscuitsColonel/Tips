# LVS（NAT 方式）+ Keepalived で負荷分散と冗長化を組むときの前提と注意点

CentOS 7 で LVS（ipvsadm）と Keepalived を使い、HTTP・SMTP・任意の TCP ポートを 2 台のバックエンドへ振り分けつつ、LVS 自体も VRRP で冗長化したときの設計判断と、手を動かして分かったこと。

（2021-08〜10 時点のメモ。CentOS 7.9、ipvsadm 1.27、keepalived 1.3.5、NAT 方式。）

## 前提

- keepalived は ipvsadm をラップしているので、LVS の設定は `keepalived.conf` だけで足りる
- NAT 方式では、LVS 側で `net.ipv4.ip_forward = 1` が必要
- NAT 方式では、バックエンドからの戻りも LVS を通す。バックエンドのデフォルトゲートウェイ（またはクライアント側セグメントへの経路）を LVS 側の VIP に向ける

## VRRP の設定

- 両ノードとも `state BACKUP`、`priority 100`、`nopreempt`。優先度が等しいと先に起動したほうが MASTER になり、`nopreempt` なので、優先度の高いノードが戻っても自動では切り戻らない
- Pacemaker の `crm_mon` のような状態確認の手段が無いので、`notify` スクリプトで状態をファイルに書き出して確認する
- `sorry_server` と `inhibit_on_failure` も設定した

### track_script で LVS 自身の疎通を見る

LVS ノード自体のネットワーク断を検知して切り替えるため、`track_script` を書いた。

1. 外部（公開 DNS など）へ `ping` を 1 回、バックエンド 2 台へ `ping` を 1 回ずつ
2. 自分が MASTER のときだけ、VIP への `ping` も足す。MASTER かどうかは、`USR2` を送って keepalived の状態をダンプし、`Became master: 1` かどうかで判定した
3. 各 `ping` の戻り値の合計を `exit` コードにし、0 以外を失敗とする。`interval 1`、`timeout 1`、`rise 3`、`fall 3`

## プロトコル別の注意

| 振り分け先 | ヘルスチェック | 注意 |
| --- | --- | --- |
| HTTP | （元メモに記載なし） | NAT の前提（上記）を満たす |
| SMTP | `SMTP_CHECK`（`connect_timeout 10`、`nb_get_retry 3`、`delay_before_retry 5`） | バックエンドの Postfix は `inet_interfaces = all` にして再起動する（既定は localhost のみ）。メールボックスは SMTP サーバが複数あっても同じ内容が見える共有ストレージに置く |
| 任意の TCP | `TCP_CHECK`（`connect_port` を指定） | ラウンドロビンは接続単位で、メッセージ単位ではない |

任意の TCP ポートの確認では、`nc -kl` で待ち受けを立てた 2 台に、クライアント 2 台から 3 回ずつ接続した。1 回目の接続は 1 台目、2 回目は 2 台目に着き、1 回目のクライアントが再接続するとまた 1 台目に戻った。振り分けは接続ごとで、メッセージごとではない。

## 手動で切り離すと、その場のノードにしか効かない

```sh
ipvsadm -d -t <VIP>:80 -r <real-server>                # 切り離し
ipvsadm -a -t <VIP>:80 -r <real-server> -m -w 1        # 戻す（NAT、重み 1）
```

切り離すと、実行したノードの `ipvsadm -Ln` から該当の real server が消える。ただし、もう一方のノードの `ipvsadm -Ln` には 2 台とも残っていた。手動の変更はノード間で同期されないので、LVS が切り替わると切り離したはずの real server が復活する。切り離したあとの既存コネクションは `InActConn` として残る（71 件残った例がある）。
