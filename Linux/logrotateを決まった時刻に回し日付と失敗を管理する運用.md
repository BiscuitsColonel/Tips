# logrotate を決まった時刻に回し、ローテート後の日付を前日にそろえ、失敗を syslog に残す

複数サーバーのログローテーションを Ansible で配布していたときの工夫のまとめ。実行時刻を固定する、ローテート後のファイル名の日付を前日にそろえる、事前に dry run で設定を検証する、失敗を `logger` に残す、の4点。アプリ名・パスは載せず、仕組みだけ書く。

（2021-10 時点のメモ。RHEL 系の OS。playbook 本体は載せない）

## 1. 実行時刻を固定する（anacron をやめる）

実行時刻を自分で決めたい場合は、`cronie-anacron` を外して `cronie-noanacron` を入れ、`/etc/cron.d/dailyjobs` で `run-parts` を自分で指定した時刻に回す。

```yaml
- name: install cronie-noanacron
  yum:
    name: cronie-noanacron
    state: latest

- name: remove cronie-anacron
  yum:
    name: cronie-anacron
    state: absent
```

```text
# /etc/cron.d/dailyjobs
SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root

# run-parts
00 0 * * * root [ ! -f /etc/cron.hourly/0anacron ] && run-parts /etc/cron.daily00
22 4 * * 0 root [ ! -f /etc/cron.hourly/0anacron ] && run-parts /etc/cron.weekly
42 4 1 * * root [ ! -f /etc/cron.hourly/0anacron ] && run-parts /etc/cron.monthly
```

日次だけ `/etc/cron.daily00/` という別ディレクトリを作って 0 時に回し、logrotate のスクリプトもそこに置く（標準の `/etc/cron.daily/` には置かない）。

## 2. ローテート後のファイル名の日付を前日にそろえる

0 時に回すと、ローテートされるのは前日分のログなのに、`dateext` が付ける日付は当日になる。`lastaction` でファイル名の日付を前日に付け替えていた。

```conf
/var/log/example/*.log {
  daily
  rotate 7
  missingok
  dateext
  dateformat .%Y%m%d
  sharedscripts
  lastaction
    for LOG_FILE in $1
    do
      /bin/mv -f ${LOG_FILE}.`date +%Y%m%d` ${LOG_FILE}.`date +%Y%m%d --date '1 days ago'`
    done
  endscript
}
```

logrotate の man には `dateyesterday`（`dateext` の日付に昨日の日付を使う）という設定値もある。このメモの時点でこちらを使っていたか、CentOS 7 の logrotate で使えるかは確認していない。

## 3. 配布前に設定を dry run で検証する

テンプレートの logrotate 設定を配るたびに、全ファイルを `-d`（デバッグ。実際にはローテートしない）で通して構文を確かめる。Ansible の事前チェック用 role に入れていた。

```sh
for i in $(ls roles/logrotate/templates/conf/*); do logrotate -d ${i}; done
```

## 4. 失敗を syslog に残す

logrotate をラッパーで呼び、異常終了なら `logger` で ALERT を出す。`/etc/cron.daily00/logrotate` に置く。

```sh
#!/bin/sh

/usr/sbin/logrotate -s /var/lib/logrotate/logrotate.status /etc/logrotate.conf
EXITVALUE=$?
if [ $EXITVALUE != 0 ]; then
    /usr/bin/logger -t logrotate "ALERT exited abnormally with [$EXITVALUE]"
fi
exit 0
```

- 最後を `exit 0` にしているので、cron のジョブとしては常に成功扱いになり、失敗の通知は syslog の ALERT に一本化される
- 状態ファイル（`-s`）は標準の cron が使う場所を指定している。別の場所にすると、ローテート済みの記録が二重管理になる
