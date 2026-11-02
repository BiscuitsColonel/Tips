# Terragrunt で tfstate をリソース単位に分割して運用するときの勘所

tfstate をネットワーク・セキュリティ・アプリのように粒度を分けて持ち、Terragrunt で全体を一度に操作するときに踏みやすい点をまとめる。

（2021-11 時点のメモ。Terragrunt 0.31〜0.32 で確認）

## 構成の考え方

環境ごとのディレクトリ（`dev`・`prod`）の下に、リソースディレクトリ（`network`・`security`・`hello-app-server`）を置く。tfstate はこのリソースディレクトリの単位で分かれる。モジュール本体は `modules/` に置き、各リソースディレクトリから `source` で参照する。

## 共通設定を親の terragrunt.hcl にまとめる

`backend` を空で書き、親の `terragrunt.hcl` の `remote_state` で上書きする。Terraform のみで分割するときのように、ほぼ同じ内容の設定ファイルを各ディレクトリに置く必要がなくなる。

```hcl
remote_state {
  backend = "local"
  config = {
    path = "${get_parent_terragrunt_dir()}/tfstate.d/${path_relative_to_include()}/terraform.tfstate"
  }
}
```

`include "root"` で親を読み込み、`source` には `path_relative_to_include()` を使って、ディレクトリ名と同じ名前のモジュールを引く。

```hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../modules//${path_relative_to_include()}"
}
```

親の `locals` で定義した値は、そのままでは子から使えない。`include` に `expose = true` を付けると `include.root.locals...` で参照できる。

```hcl
include "root" {
  path   = find_in_parent_folders()
  expose = true
}
```

## 別ディレクトリの出力を受け取る

`data "terraform_remote_state"` の代わりに `dependency` ブロックと `inputs` を使う。

```hcl
dependency "network" {
  config_path = "../network"
}

inputs = {
  vpc-id = dependency.network.outputs.vpc-id
}
```

出力値を受け取らず、実行順だけ指定したいときは `dependencies` ブロックを使う。

## プラグインのディスク使用量を減らす

tfstate を分割すると、ディレクトリごとに `.terraform` 配下へプロバイダがダウンロードされる。AWS プロバイダは Mac で 200MB 以上あり、ディスクを使う。`~/.terraformrc` に `plugin_cache_dir` を設定すると、プラグインの実体が1か所にまとまり、各ディレクトリはそこへのリンク（103 byte）になった。ディレクトリは自動作成されないので先に作る。

```sh
$ cat ~/.terraformrc
plugin_cache_dir = "$HOME/.terraform.d/plugin-cache"
$ mkdir -p $HOME/.terraform.d/plugin-cache
```

ミラーやキャッシュ経由で入れるとロックファイルに記録されるハッシュが変わる点は、[プロバイダのロックファイルのzhとh1.md](プロバイダのロックファイルのzhとh1.md) を参照。

## ほかの点

- `terragrunt run-all apply` は、各ディレクトリで `init` を自動で実行するので、明示的に `run-all init` する必要はない。実行中に出る `WARN No double-slash (//) found in source URL` は、サブモジュールを使っていなければ無視してよかった
- `terragrunt graph-dependencies` の出力を `dot` に渡すと、`[INFO]` のログ行が混ざって構文エラーになる。`grep -vF '[INFO]'` で取り除く（`grep -v "[INFO]"` の `[INFO]` は文字クラスとして解釈され、`I`・`N`・`F`・`O` のどれかを含む行がすべて消えてしまう。`-F` で固定文字列にする）
- Terragrunt のリポジトリの `.gitignore` には `.terraform.lock.hcl` が書かれているが、Terraform 公式ではコミットが推奨されている。ignore から外したほうがよい
- `.terraform-version`（tfenv）と `.terragrunt-version`（tgenv）をディレクトリに置くと、そのディレクトリ配下だけバージョンを固定できる

```sh
$ tgenv list
* 0.31.8 (set by /Users/tester/.tgenv/version)
  0.31.5
$ echo 0.31.5 > .terragrunt-version
$ terragrunt --version
terragrunt version v0.31.5
```
