# Session Manager を IP 制限する IAM ポリシーと、Patch Manager でインスタンスを一時的に対象外にする方法

（2021-11 時点のメモ）SSH や RDP で入っていたサーバーの管理を Session Manager へ切り替えるときに、送信元 IP の制限をどう移すか。それと、パッチ適用の対象外にする方法。

## Session Manager の IP 制限は IAM ポリシーで行う

SSH/RDP のときはセキュリティグループで接続元 IP を絞っていた。Session Manager はポートを開けずに IAM で接続を許可するので、IP 制限も IAM ポリシーの `aws:SourceIp` で書く。

許可を IP で絞る例（`ssm:StartSession` は、ノーマル・ポートフォワード・SSH のどれでも使う）。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession",
        "ssm:TerminateSession",
        "ssm:ResumeSession",
        "ssm:DescribeSessions",
        "ssm:GetConnectionStatus"
      ],
      "Resource": ["*"],
      "Condition": {
        "IpAddress": { "aws:SourceIp": ["192.0.2.0/24", "203.0.113.0/24"] }
      }
    }
  ]
}
```

別のポリシーで広い範囲の `ssm:StartSession` を許可していると、この Allow があっても制限にならない。IAM は複数のポリシーの Allow を合算するからである。確実に締めるなら、同じ Action に `NotIpAddress` 条件の Deny を付ける。

```json
{
  "Effect": "Deny",
  "Action": ["ssm:StartSession", "ssm:TerminateSession", "ssm:ResumeSession", "ssm:DescribeSessions", "ssm:GetConnectionStatus"],
  "Resource": ["*"],
  "Condition": {
    "NotIpAddress": { "aws:SourceIp": ["192.0.2.0/24", "203.0.113.0/24"] }
  }
}
```

通常の Session Manager・ポートフォワード・SSH 接続のどれも `ssm:StartSession` で始まるので、3 種類を別々に制限する必要は無い。IP 制限に引っかかると、`aws ssm start-session` が `AccessDeniedException ... is not authorized to perform: ssm:StartSession` を返す。SSH 経由の場合は、そのあとに `Connection closed by remote host` が続く。

## Patch Manager で特定のインスタンスだけを対象外にする

パッチ適用の設定が、パッチグループのタグ（`Patch Group`）で対象を決めている場合、対象外にしたいインスタンスのタグの値を変える。

```
Patch Group : Amazon Linux 2   →   Patch Group : Amazon Linux 2 jogai
```

メンテナンスウィンドウの対象は、元のタグの値と一致するインスタンスなので、値を変えたインスタンスは次の実行から外れる。一時的に止めたい運用に向く。

Terraform でタグを管理しているときは、`apply` するとタグが元に戻って、対象外が解除される。`lifecycle.ignore_changes = [tags]` を付けるか、Terraform を回す前に確認する。
