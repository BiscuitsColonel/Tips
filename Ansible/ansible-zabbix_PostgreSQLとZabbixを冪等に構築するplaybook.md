# 自作 playbook「PostgreSQL + Zabbix 構築」: 何をするものか、冪等にした書き方、bash 履歴の syslog 化

PostgreSQL（Zabbix のバックエンド）、Zabbix サーバ、エージェント、PostgreSQL 監視用の設定を、`site.yml` から role を並べて適用する自作プロジェクト。コード全体は置かず、冪等にするために選んだ書き方と、手間のかかった bash の履歴ログ設定を残す。

（2022-10〜11 時点のメモ。Ansible 2.9、パッケージは `dnf` で導入。）

## 構成と使い方

- role: `os_common`（共通パッケージ）、`bash`、`postgres`、`postgres_rman`、`zabbix-server`、`zabbix-agent`、`zabbix-postgres`
- `site.yml` で全体、`site_bash1.yml` と `site_zabpos.yml` で role 単独を、タグ付きで適用する

```sh
ansible-playbook -i hosts site.yml
ansible-playbook -i hosts site_zabpos.yml
```

## 冪等にした書き方

再実行しても changed が出ないように、1 回きりの処理をそれぞれ次の形で守った（コマンドの中身は例）。

```yaml
# initdb は、できあがるファイルの有無で守る（PGDATA が2通りある環境でも同じ形で守れるかは、元の playbook の記述。未確認）
- command: postgresql-setup --initdb
  args:
    creates: "{{ pgdata }}/postgresql.conf"

# module disable は、出力に変更を示す文言があったときだけ changed（再実行時の出力に同じ文言が出ないかは、元の playbook の記述。未確認）
- command: dnf -y module disable postgresql
  register: result
  changed_when: '"Disabling modules" in result.stdout'

# Zabbix の初期スキーマは、流した印のファイルで 1 回だけにする（印のファイルの置き場所は、元の playbook の記述。未確認）
- shell: zcat create.sql.gz | psql -U zabbix zabbix && touch create.sql.executed
  args:
    creates: create.sql.executed
```

- 監視用ユーザーに `pg_monitor` を `GRANT` し、`pg_hba.conf` には `insertbefore: BOF` で先頭に 1 行足す。`pg_hba.conf` は先に一致した行が効くので、順序に意味がある。接続元は `127.0.0.1/32` に限る
- PGDATA の場所が 2 通りある環境（単独とクラスタ）は、`stat` の結果を `when` で分岐させる
- 設定ファイルの既定値の行は `lineinfile` の `regexp` で置き換える（Agent の `Hostname`・`Server`・`ServerActive`、PHP の `date.timezone` を `Asia/Tokyo` に。タイムゾーンは `php.ini` と `php-fpm.d/zabbix.conf` の 2 か所）。Hostname は `inventory_hostname` を使う
- ホストごとに違う設定は `{{ inventory_hostname }}-<file>.j2` を引く

PostgreSQL 用の `UserParameter` は、同じ型で書くと SQL ファイルを増やすだけで済む。

```text
UserParameter=pgsql.xxx[*], psql -qtAX -h "$1" -p "$2" -U "$3" -d "$4" -f /path/xxx.sql
```

エージェントの環境ファイルに `LANG=C` を入れ、`PATH` に PostgreSQL の `bin` を足しておく。

## bash のコマンド履歴を syslog に残す（role: bash）

履歴を syslog に出す機能は bash のコンパイル時オプション（`SYSLOG_HISTORY`）なので、ソースから再ビルドする。ビルド後のログ出力まで一式で要る。

1. bash 4.4.18 のソースを取得し、`config-top.h` を `lineinfile` で書き換える
   - `/* #define SYSLOG_HISTORY */` のコメントを外す
   - `SYSLOG_FACILITY` を `LOG_LOCAL6`、`SYSLOG_LEVEL` を `LOG_INFO` にする
2. ビルドしたバイナリを入れ、`/etc/shells` に追記して、ログインシェルを変更する
3. auditd の syslog プラグインを `active = yes`、`args = LOG_LOCAL5` にする
4. rsyslog に local3 / local5 / local6 の出力先を足す（local5 は auditd、local6 は bash 履歴。local3 の用途は、元の playbook の記述。未確認）
5. logrotate の syslog 設定に、履歴ログのファイルを足す

ビルド一式は、`stat` で成果物の有無を調べて `block` ごと `when: not exists` にし、`unarchive` にも `creates` を付けて冪等にした。
