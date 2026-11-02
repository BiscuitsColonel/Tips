# PowerGres（PostgreSQL 派生製品）の運用で踏んだ問題と対処

PostgreSQL 派生の商用製品 PowerGres Plus と、その管理ツール（Administration Tool）を運用していて出た問題の記録。製品固有の挙動なので、PostgreSQL 本体の話ではない。

（2020〜2021 年ごろのサポート問い合わせの記録。PowerGres 9.4〜11 系、一部は Windows 版）

## 管理ツールのログイン画面が `An Internal Error Has Occurred.`

- 現象: ログイン画面を開くと内部エラー。管理ツールのエラーログに `Table servers for model Server was not found in datasource default.`
- 分かったこと: 管理ツールが使うフレームワークのキャッシュを消しても変わらなかった。設定用の SQLite ファイル（`default.sqlite`）が壊れているとこのエラーになる。
- 対処: 管理ツール同梱の `Console\cake.bat` で、`schema create --yes`、`user add`、`server_profile add --pgconfig ...\pg_config.exe` を順に実行して `default.sqlite` を作り直す。改善する見込み、という回答で、結果は記録に無い。

## Linux 版をアップデートすると管理ツールが文字化けする

既知の不具合。アップデート時に古い PHP キャッシュが残るのが原因で、管理ツールのキャッシュディレクトリ（`tmp/cache` の `models`、`persistent`、`views`）のファイルを消すと直る。DB のデータには影響しない。次のバージョンで修正される予定だった。

## RHEL 8 へのインストールが管理ツールの段階で止まる

本体のインストールには成功するが、管理ツールのパッケージが `nothing provides libzip.so.5()(64bit)` で止まる。一度アンインストールし、`libzip` を入れてからやり直す。ほかに `libicu`、`libxslt`、`perl` を先に入れておく（PHP は製品に含まれるので不要）。

## 自動起動

- `systemctl list-unit-files --type=service | grep powergresplus10` が `disabled` なら `systemctl enable` で起動時に自動開始する。
- 管理ツールからの起動・停止と `systemctl` は管理が独立している。`systemctl` で起動すると管理ツールからも状態が分かるが、管理ツールから起動・停止すると `systemctl` が状態を認識できなくなる。どちらかに統一する。
- 起動時のログに `"/var/lib/pgsql/10/data" is missing or empty.` が出て起動しないのは、データディレクトリを標準の場所から移しているのにユニットファイルがそのままのとき。`/etc/systemd/system/powergresplus10.service` の `Environment=PGDATA=` を実際の場所に直し、`systemctl disable` と `enable` をやり直す。

## 透過的暗号化のキーストアが開かない

- 現象: ある時点から DB にアクセスできず、`FATAL: could not encrypt or decrypt data because the keystore is not open`。
- 原因: キーストアの自動オープンが無効だと、再起動のたびにキーストアを手動で開く必要がある。
- 自動オープンを有効にしていても、ハードウェアや OS の設定を変えたときに使えなくなることがある。その場合は自動オープンを一度解除して、もう一度有効にする。

## バックアップの暗号化

暗号化したバックアップを取れるのは、透過的暗号化を有効にした上での「オンラインバックアップジョブ」（内部では `pgx_dmpall`）。「バックアップジョブ」は内部で `pg_dump` / `pg_dumpall` を使うので暗号化できない。

## コールドスタンバイ機でバックアップジョブがエラーになる

- 現象: Pacemaker ＋ DRBD のコールドスタンバイ構成で、待機機のバックアップが `pg_controldata: could not open file ".../global/pg_control"` で失敗する。
- 原因: 稼働機が動いている間、待機機には PostgreSQL のデータが見えない（起動していない）から。
- 対処: 管理ツールがバックアップジョブに連動して cron に登録するスクリプトを `crontab -e` で直接編集し、`[ -d データディレクトリ ] && 元のコマンド` にする。ただし、これでそのジョブは管理ツールの管理から外れ、一覧に出なくなる。時刻を変えるときも cron を直接直すことになる。

## Windows でサービス登録が `error code 1057`

`pg_ctl: could not register service ...: error code 1057` は、入力した Windows のユーザー名かパスワードの誤り。管理ツールの画面で失敗するときは、管理者権限のコマンドプロンプトで `pg_ctl.exe register -N サービス名 -U ユーザー -P パスワード -D データディレクトリ` を実行して切り分ける。
