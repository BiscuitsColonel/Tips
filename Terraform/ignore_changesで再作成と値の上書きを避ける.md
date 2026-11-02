# Terraform の ignore_changes で RDS の再作成や秘密値の上書きを避ける

作成後に Terraform の管理外で変わる値（手で変えるパスワード、AWS が決める属性）が原因で、差分が出続けたり再作成になったりするのを `lifecycle.ignore_changes` で避ける。

（2021-11 時点のメモ）

## Aurora クラスタで再作成される場合

`aws_rds_cluster` を作った後、設定以外の変更や、再作成が不要な変更をしても、クラスタを作り直そうとする差分が出ることがあった。回避策は `master_password` と `availability_zones` を `ignore_changes` に入れて Terraform の管理から外すことだった。既知の問題で、この設定以外に回避方法は見つからなかった。

```hcl
resource "aws_rds_cluster" "main" {
  cluster_identifier = "aurora-cluster"
  engine             = "aurora-mysql"
  availability_zones = ["ap-northeast-1a", "ap-northeast-1c"]
  master_username    = "masteruser"
  master_password    = var.db_password

  lifecycle {
    ignore_changes = [
      master_password,
      availability_zones,
    ]
  }
}
```

## 最初の apply だけ値を渡し、以後は変数を渡さない

DB パスワードのような値を Secrets Manager に入れる場合、plan や apply のたびに `var.db_password` を手元で用意するのは面倒だった。次の組み合わせにすると、最初の apply だけ値を渡せば、2回目以降は渡さずに済む。

- `variable` の `default = null` にする。値を設定しなかった変数は `null` になる
- 値を受けるリソースの引数（ここでは `secret_string`）を `ignore_changes` に入れる

```hcl
variable "db_password" {
  type    = string
  default = null
}

resource "aws_secretsmanager_secret" "main" {
  name = "main"
}

resource "aws_secretsmanager_secret_version" "main" {
  secret_id     = aws_secretsmanager_secret.main.id
  secret_string = jsonencode({ db_password = var.db_password })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
```

```sh
$ export TF_VAR_db_password=xxxxxxxx   # 最初の apply だけ
$ terraform apply
```

`ignore_changes` は変更を無視するだけでリソース自体は生成されるので、初回に渡した値でシークレットが作られる。

比べて捨てた方法は2つ。

- 環境変数 `TF_VAR_...` を毎回設定する: ターミナルを開き直すたびに入力が要る
- 値を `terraform.tfvars` に書いて gitignore する: 複数人で開発すると、更新された値に気づかず、手元の古い値で上書きしうる

どちらの方法でも、初回に渡した値は tfstate に平文で残る。tfstate に載せないなら、RDS・Aurora の `manage_master_user_password` か、Terraform 1.11 以降の write-only 引数（[公式ドキュメント](https://developer.hashicorp.com/terraform/language/manage-sensitive-data/write-only)）を使う。

## 参考

- [Resource Behavior: lifecycle ignore_changes](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle#ignore_changes)
