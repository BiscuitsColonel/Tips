# RPM と systemd で PostgreSQL・pgpool-II を運用するときに踏みやすい点（daemon-reload、contrib、pgpool_status）

RPM で入れた PostgreSQL と pgpool-II を systemd で動かす環境で、設定変更が効かなかった点と、pgpool-II の 2 台構成でレプリケーションが切れたときの復旧のメモ。

（2021-07〜2022-01 時点のメモ。PostgreSQL 10〜12、CentOS 7 系の環境）

## unit ファイルを直したら daemon-reload が要る

unit ファイルを編集しただけでは反映されず、次の警告が出る。

```
Warning: pgpool.service changed on disk. Run 'systemctl daemon-reload' to reload units.
```

編集後は `sudo systemctl daemon-reload` を実行してから再起動する。起動コマンドは `systemctl cat <サービス名>` の `ExecStart` で確認できる。

PostgreSQL 12 の PGDG パッケージの unit ファイルは、冒頭のコメントでパッケージ更新時に上書きされるので直接編集しないよう案内している。drop-in（`/etc/systemd/system/postgresql-12.service.d/` に `.conf` を置く）か `systemctl edit postgresql-12` で上書きする。`PGDATA` を変えるときは `Environment=PGDATA=...` を上書きして、同じく `daemon-reload` する。コメントには、PGDATA を変えると SELinux の設定も要ること、PGDATA にスペースを含めないこと、`TimeoutSec=0` はクラッシュリカバリ中に systemd に殺されないための設定であることも書かれている。

## contrib は初期構築のときに入れておく

`pgstatindex` などを持つ `pgstattuple` は contrib パッケージに入っている。運用を始めたあとに `yum install` すると、DB サーバーのマイナーバージョンも一緒に上がってしまった。使う可能性のある contrib は構築時に入れておく。

## pgpool-II の 2 台構成で、片方にしか書き込まれなくなった

状況は次のとおり。

- 2 号機にしか書き込みが行われていない。サービスは上がっていて、レプリケーション失敗のログも出ていない
- 1 号機の OS が（こちらの意図なく）再起動していた

最初は 1 号機の再起動中に 2 号機へ更新が入って DB に差異ができたと考え、2 号機の DB を 1 号機へリストアしたが、直らなかった。

原因は `/var/log/pgpool/pgpool_status` が 1 号機を down のまま記録していたことだと仮定し、pgpool の起動コマンドに `-D` を足した。`-D` は前回の `pgpool_status` を捨てて作り直して起動するオプション。unit ファイルの `ExecStart` に足して `daemon-reload` し、再起動したところ、`pgpool_status` が up / up になり、書き込みが両方に行くようになった。

このときは、1 号機が復旧しても pgpool 側の status が戻らなかった。`-D` を足したら直ったので、原因は `pgpool_status` だったと推定している（`-D` 以外の要因は切り分けていない）。レプリケーション自体に問題がなさそうなときは、`pgpool_status` を疑う。

注意: `-D` を常に付けておく運用は避ける。再起動のたびに前回の status を捨てて全ノードを up として扱うので、データが追いついていないノードが up で戻り、古い内容のまま読み書きの対象になる危険がある。付けるのは、ノードの内容が揃っていると確かめたうえで、1 回だけにする。
