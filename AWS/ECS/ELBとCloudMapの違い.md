# ECS のサービス間通信：ELB と Cloud Map（サービス検出）の違い

デプロイ直後とタスクのドレイン中に差が出る。

| 場面 | Cloud Map（DNS ベースのサービス検出） | ELB |
| --- | --- | --- |
| デプロイ直後 | DNS キャッシュが残っている間、停止した旧タスクの IP へ接続しに行くことがある。リトライしていなければエラーになる | 旧タスクはターゲットから外れているので、旧タスクへは振られない |
| ドレイン中 | ドレイン中のタスクにも振られることがある（ドレイン中も通常どおり応答するのでエラーにはならない） | 登録解除した時点で新しいリクエストは振られない。処理中のリクエストが終わるまで `draining` 状態になる |

DNS ベースのサービス検出を使うなら、クライアント側でリトライを入れ、DNS の TTL を短くしておく。

## Service Connect

2022-11 に ECS Service Connect が追加された。名前解決は Cloud Map を使うが、各タスクに入るプロキシ（Envoy）が接続先を管理するため、DNS キャッシュによる旧タスクへの接続が起きにくい。リトライや外れ値の検出もプロキシ側で行う。ECS のサービス同士の通信だけで完結するなら、DNS ベースのサービス検出より Service Connect を先に検討する。

- [Amazon ECS Service Connect](https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/service-connect.html)
