# CloudWatch Agent の設定ウィザードで詰まる点（collectd の types.db エラーとパラメータストア名）

CloudWatch Agent の設定ウィザード（`amazon-cloudwatch-agent-config-wizard`）を CentOS 系の EC2 で実行し、設定を SSM パラメータストアへ保存して配るときに、実際に引っかかる 2 点のメモ。

（2021-11 時点のメモ）

## collectd を「yes」にすると起動時に types.db のエラーが出る

ウィザードの `Do you want to monitor metrics from CollectD?` に `1 (yes)` を選ぶと、エージェント起動時に次のエラーになる。

```text
open /usr/share/collectd/types.db: no such file or directory
```

原因は、OS に collectd のパッケージが入っていないこと。collectd を使わないなら `2 (no)` を選ぶ。使うなら EPEL を有効にしてから collectd を入れる。EPEL の有効化手順は AWS の次のナレッジセンターを参照する。

https://aws.amazon.com/jp/premiumsupport/knowledge-center/ec2-enable-epel/

## パラメータストアの名前は `AmazonCloudWatch-` で始める

ウィザードの最後で `Do you want to store the config in the SSM parameter store?` に `yes` と答えると、保存先の名前を聞かれる。AWS 管理ポリシー（`CloudWatchAgentServerPolicy` など）を EC2 のロールに付けている場合、読み書きできるパラメータは `AmazonCloudWatch-*` に限られる。これ以外の名前を付けると、パラメータの読み書きに失敗する。ウィザードの既定値（`AmazonCloudWatch-linux`）のように、この接頭辞を付ける。

## 設定の反映

ウィザードで作った設定は `/opt/aws/amazon-cloudwatch-agent/bin/config.json` にも保存される。SSM から取得して起動するときは次を使う。

```sh
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:AmazonCloudWatch-linux -s
```

`-a append-config` は既存の設定に追記する。置き換えたいときは `fetch-config` を使う。
