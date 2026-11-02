# .terraform.lock.hcl の zh と h1 の違いと、複数プラットフォームで checksum が合わないときの考え方

Terraform 0.14 で入った `.terraform.lock.hcl` に記録されるハッシュには `zh` と `h1` の2種類がある。違いを知っておくと、手元は macOS で CI は Linux のような環境で起きる checksum の不一致を説明できる。

（2021-11 時点のメモ。Terraform 0.14 系で確認）

## zh と h1

| 種類 | 中身 |
| --- | --- |
| `zh:` | Registry が配るプロバイダの zip のハッシュ。Registry のオリジンから取ったときは、全プラットフォーム分がまとめて記録される |
| `h1:` | 実際に取り込んだプラットフォームのバイナリのハッシュ |

通常は `terraform init` で、最初に実行したプラットフォームの `h1` しか記録されない。プラットフォームが混在する環境では checksum の不一致が起きる。

公式ドキュメントでは、`zh` は旧形式、`h1` は現在推奨の形式とされている。Registry のオリジンから入れると zh が全プラットフォーム分、h1 が実行環境の分だけ入る。あらかじめ両方を作るには `terraform providers lock -platform=...` を使う（[Dependency Lock File](https://developer.hashicorp.com/terraform/language/files/dependency-lock)）。

## ミラーやキャッシュから入れた場合

ローカルミラー（`terraform providers mirror` で作る）やキャッシュから入れると、`zh` は記録されず `h1` だけが記録されるように見えた。公式ドキュメントも、ミラーなど別の方法で最初に入れると、`init` を実行したプラットフォームの分しか検証・記録できないと説明している。

## 迷って選んだこと

複数ディレクトリがあるリポジトリで、全ディレクトリのロックファイルを効率よく複数プラットフォーム対応で作る方法を考えた。

- ディレクトリごとに `terraform providers lock` や `init -upgrade` を回すと、プロバイダのダウンロードが重複する
- ミラーを作る時点でバイナリの署名は検証される。その時点で生成された `h1` をロックファイルに書き込めば、`zh` を使わなくても実害はないと判断した。`zh` は記録せず `h1` だけを使うのが現実的な最適解、というのが当時の結論だった

## 気になった挙動

`h1` だけが記録され、キャッシュも何もない状態で `terraform init`（`-upgrade` なし）を実行すると、ロックファイルに `zh` が追記された。バグか仕様か判断できなかった。

## provider ブロックの version

0.13 以降は `required_providers` の `source` と `version` で指定する。provider ブロックの `version` は非推奨で、メモ当時（0.14）は警告が出ていた。
