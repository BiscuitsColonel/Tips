# CDK（TypeScript）の L1 コンストラクトで ALB と Auto Scaling グループを組み、userdata に設定ファイルを埋め込む

既存の VPC に、EC2 を ASG で 2 台並べて ALB 配下に置く構成を、CDK の `Cfn*`（L1）だけで書いたときの構成と、userdata に設定ファイル一式を渡す工夫のメモ。同じ構成を素の CloudFormation でも書いた。

（2022-01 時点のメモ。CDK v1 系）

## 構成

- VPC・サブネット・SG は新規に作らず、既存の ID を定数で渡す。ネットワークはこのスタックの管理外
- `CfnLoadBalancer`（internet-facing の ALB）、`CfnTargetGroup`（HTTP 80）、`CfnListener`（80 を転送）、`CfnLaunchTemplate`、`CfnAutoScalingGroup` を直接組む
- 名前は `${ProjectName}-${Environment}-alb` のように揃え、`Name` と `Environment` タグを全リソースに付ける。ASG のタグだけは `propagateAtLaunch: true` にしてインスタンスへ伝播させる

## 決めた値

| 対象 | 値 |
| --- | --- |
| ASG | min = max = desired = 2、AZ は 1a と 1c、`cooldown` 300、`healthCheckType: ELB`、`healthCheckGracePeriod` 300 |
| ターゲットグループ | ヘルスチェック間隔 30 秒、タイムアウト 5 秒、healthy / unhealthy ともに 5 回、成功コード 200 |
| ターゲットグループ属性 | 登録解除の遅延 300 秒、スティッキネスは `lb_cookie`（有効化フラグは false）、ロードバランシングは `round_robin` |
| ALB 属性 | アイドルタイムアウト 60 秒、`routing.http.desync_mitigation_mode` は `defensive`、削除保護とアクセスログは無効 |

## userdata に設定ファイルを埋め込む

httpd の設定や監視エージェントの設定を userdata から配置するため、リポジトリ内の設定ファイルを読み込んで heredoc のコマンド文字列に変換し、userdata のひな形の `CONFS` という目印と置き換えている。

```typescript
const confFile = fs.readFileSync('./lib/userdata/httpd/conf/httpd.conf', 'utf8');
const confCommand = 'cat <<EOF > /etc/httpd/httpd.conf\n' + confFile + 'EOF\n';

// conf.d 配下は全ファイルを順に heredoc 化する
let includeCommand = '';
for (const name of fs.readdirSync('./lib/userdata/httpd/conf.d/', 'utf8')) {
  const body = fs.readFileSync('./lib/userdata/httpd/conf.d/' + name, 'utf8');
  includeCommand += 'cat <<EOF > /etc/httpd/conf.d/' + name + '\n' + body + 'EOF\n';  // += で連結する
}

const userData = userDataTemplate.replace('CONFS', confCommand + includeCommand);
// ... launchTemplateData: { userData: cdk.Fn.base64(userData) }
```

注意点。

- メモのコードは、ループ内の連結を `=` で書いていたため、`conf.d` の最後のファイルしか残らない書き方になっていた（コードを読み返して気づいた点。実機での再現はしていない）。複数ファイルを渡すなら `+=` にする
