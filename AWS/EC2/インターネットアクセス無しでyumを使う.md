# インターネットアクセスの無い EC2 で yum を使う（S3 の Gateway 型 VPC エンドポイント）

（2021-11 時点のメモ）NAT Gateway も Internet Gateway も無いプライベートサブネットの Amazon Linux で、`yum` を通す方法。Amazon Linux のパッケージリポジトリは S3 に置かれているので、S3 の VPC エンドポイントがあれば取得できる。

## 手順

1. VPC のエンドポイントで `com.amazonaws.ap-northeast-1.s3` を作る。タイプは Gateway 型にする（Interface 型は料金がかかる。Gateway 型は無料）
2. 対象の EC2 が属するサブネットのルートテーブルを関連付ける
3. ポリシーは「フルアクセス」でも動く。絞るなら、リージョンのリポジトリ用バケットの `GetObject` だけを許可する

```json
{
  "Statement": [
    {
      "Principal": "*",
      "Action": ["s3:GetObject"],
      "Effect": "Allow",
      "Resource": ["arn:aws:s3:::amazonlinux.ap-northeast-1.amazonaws.com/*"]
    }
  ]
}
```

この `Resource` は Amazon Linux 1・2 のものである。Amazon Linux 2023 のリポジトリは `al2023-repos-<リージョン>-de612dc2` という別のバケットにある（[AL2023 ユーザーガイド](https://docs.aws.amazon.com/linux/al2023/ug/managing-repos-os-updates.html) の `dnf repolist -v` の出力例、および [Knowledge Center](https://repost.aws/knowledge-center/ec2-al1-al2-update-yum-without-internet)）。AL2023 で絞るときは、`Resource` をそのバケットの `/*` にする。

## 他に必要な設定は無かった

- Gateway 型にはセキュリティグループが無い。EC2 側のセキュリティグループはアウトバウンドの HTTP（80）が通れば足りる
- ネットワーク ACL は、アウトバウンド 80 と、エフェメラルポート（1024-65535）のインバウンドを許可する。既定の ACL（全許可）なら何もしなくてよい
- ACL に S3 の CIDR を書く場合、S3 の IP 範囲はいつでも変わる。ACL はプレフィックスリストを使えないので、`0.0.0.0/0` にするか、変更を追う運用を決める
