# Pacemaker・DRBD・corosync の異常を、重み付きの整数 1 つにして Zabbix へ送る

クラスタの複数の異常（リソースの故障、DRBD の切断、corosync のリング断など）を、異常ごとに桁を決めた整数 1 つにして `zabbix_sender` で送り、トリガ側は末尾の桁を正規表現で見て「何が悪いか」を判別する。項目の数を増やさずに、`crm` 系コマンドの結果を監視できる。

（2020-05〜10 時点のメモ。Pacemaker + DRBD + PostgreSQL の 2 ノード構成、Zabbix は `zabbix_sender` によるトラッパー項目。）

## 仕組み

1. クラスタが正常なときに `crm_mon -rfD1` の failcount 行をファイルに保存して、基準にする。基準は正常と確認した直後に 1 回だけ作る
2. 10 分ごとの cron で現在の出力と基準を `diff` し、差分があれば異常とみなす
3. 異常の種類ごとに重みを足す。pgsql = 1、VIP = 20、DRBD = 300、マウント = 4000。合計を `custom.failcount.status` というトラッパー項目に 1 回送る
4. トリガは桁ごとに分ける

| トリガの条件 | 意味 |
| --- | --- |
| `regexp(1$)` | pgsql の異常 |
| `regexp(2.$)` | VIP の異常 |
| `regexp(3..$)` | DRBD の異常 |
| `regexp(4...$)` | マウントの異常 |

`crm` コマンドは root でしか動かないので、root の cron で動かす。異常が複数同時に起きても、足し算なので桁ごとに分かれて表示される。

## DRBD と corosync も同じ方式で符号化する

別の項目（`custom.drbd.status`、`custom.corosync.status`）に、同じ考え方で送る。

- DRBD: `drbdadm cstate all` に `Connected` が無ければ 1、`drbdadm dstate all` に `UpToDate/UpToDate` が無ければ 20 を足す
- corosync: `corosync-cfgtool -s` で、ring k が `no faults` でなければ、ring 番号に応じた重みを足す（ring0 の異常は 1、ring1 の異常は 20 にして、`regexp(2.$)` で ring1 を検知）

`proc.num[pacemakerd]=0` は、別のトリガにしておく。

## 通知まわり

failcount（情報レベル）は、復旧メールを送らない設定にした。
