# NLB はクロスゾーン負荷分散が無効だと、稼働中のターゲットが無い AZ に振られて通信が失敗する

（2021-10 時点のメモ）NLB の背後のターゲットが一部の AZ にしか稼働していないとき、クロスゾーン負荷分散を有効にしないと一部の通信だけがタイムアウトする。その原因の切り分けと対処の記録。

## 起きたこと

外部のクライアントから、3 AZ（a・c・d）に配置した NLB 経由で、片系（AZ-a）だけが稼働している待機構成のサーバーへ疎通テストをした。テストの一部だけが成功し、残りは通信できなかった。NLB のクロスゾーン負荷分散を有効にすると、全てのテストが成功した。

## 原因

NLB は AZ ごとにノード（IP アドレス）を持ち、その DNS 名は複数の IP を返す。クライアントは DNS ラウンドロビンでどれかのノードに接続する。

クロスゾーン負荷分散が無効のとき、各ノードは自分と同じ AZ のターゲットにしか振らない。ターゲットが稼働していない AZ のノードに当たった通信は、振り先が無くタイムアウトする。稼働している AZ のノードに当たった通信だけが成功する。そのため、結果が「通ったり通らなかったり」になる。

```sh
$ nslookup example-nlb-0123456789abcdef.elb.ap-northeast-1.amazonaws.com
Addresses: 10.0.1.10   # AZ-a のノード
           10.0.2.10   # AZ-c のノード
           10.0.3.10   # AZ-d のノード
```

クロスゾーン負荷分散を有効にすると、どの AZ のノードに当たっても、正常（Healthy）なターゲットのどれかに振られる。

## 押さえる点

- 症状は「間欠的に通らない」になるので、アプリやファイアウォールを疑いやすい。`nslookup` で NLB のノードが何個あり、どの AZ にターゲットがいるかを先に見ると早い
- 無効のままだと、ターゲットが全 AZ に均等にいても AZ ごとの負荷が偏る。各ノードがほぼ同じ割合でリクエストを受けるので、AZ 内のターゲット数が違えば 1 台あたりの負荷が違う
- 有効にすると AZ をまたぐ通信が発生し、NLB とターゲットが別 AZ の場合は AZ 間のデータ転送料がかかる（[AWS ブログ](https://aws.amazon.com/blogs/networking-and-content-delivery/exploring-data-transfer-costs-for-aws-network-load-balancers/)）
- ターゲットを片系で待機させる構成（Active/Standby）では、有効にするのが前提になる

Terraform なら `aws_lb` の `enable_cross_zone_load_balancing = true`。

- [Network Load Balancer のクロスゾーン負荷分散](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/network-load-balancers.html#cross-zone-load-balancing)（既定は無効、NLB ノードは有効化した AZ ごとに 1 つの IP を持つ）
