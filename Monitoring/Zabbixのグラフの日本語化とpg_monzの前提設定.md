# Zabbix のグラフを日本語にする設定と、pg_monz で PostgreSQL / Pgpool-II を監視する前提設定

Zabbix の運用で実際に踏んだ、グラフの文字化けと、pg_monz のテンプレートを動かすための前提設定。

（2020-02〜10 時点のメモ。）

## グラフが日本語にならない

日本語フォントを配置して、Zabbix の画面側の設定を `graphfont` から差し替える。

```sh
ln -s <ipa-pgothic のフォントファイル> /usr/share/zabbix/fonts/ipagp.ttf
```

`/usr/share/zabbix/include/defines.inc.php` の `ZBX_GRAPH_FONT_NAME` と `ZBX_FONT_NAME` を `ipagp` に変える。

サーバがインターネットに出られない場合は、別のマシンで `yum install --downloadonly --downloaddir=./ ipa-pgothic-fonts` で rpm を取り、アップロードして `yum localinstall` する。元メモには、あとで `yum install zabbix-web-japanese` で足りた可能性に気付いたとあるが、未検証。

## pg_monz で PostgreSQL / Pgpool-II を監視する

- pg_monz は、zabbix-agent を入れたときと同じリポジトリから入れ、バージョンをそろえる
- エージェントの設定は `EnableRemoteCommands=1` と `AllowRoot=1`。`psql` が無いと言われる場合の対策として、systemd のユニットも `User=root` / `Group=root` にしている
- `postgresql.conf` は `log_file_mode = 0644` にする
- `pgsql_funcs.conf` の `PGHOME` と `PATH` は必須
- パスワードが要るときは `PGPASSFILE` で指すファイルを用意し、`chmod 600` にする
- テンプレートの XML はすべて順番にインポートし、そのあとでマクロを調整する

接続数を数える自作の監視では、PostgreSQL 10 以降で `pg_stat_activity` に `backend_type = 'client backend'` の条件を付けて、バックグラウンドプロセスを除いている。
