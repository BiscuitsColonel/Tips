# bash を SYSLOG_HISTORY 付きで再コンパイルし、全ユーザーのコマンド履歴を rsyslog に残す

サーバー上で実行されたコマンドを、ログに残したいときの方法。bash のソースを `SYSLOG_HISTORY` 有効でビルドし直し、履歴を syslog 経由で専用ログファイルに書く。

（2019-09 時点のメモ。bash 4.4.18、RHEL 系（systemd）の OS で検証。現行の OS のパッケージ版 bash が同じオプションでビルドされているかは確認していない）

## 流れ

1. 標準の bash とは別に、`/usr/local/bin/bash` として新しい bash をビルドして入れる
2. rsyslog で履歴用の facility を専用ファイルに振り分ける
3. `/etc/shells` に新しい bash を登録し、ユーザーのログインシェルを `chsh` で切り替える
4. 専用ログを logrotate の対象にする

## 1. bash のビルド

`config-top.h` で履歴の syslog 出力を有効にし、facility と level を変更する。標準では facility が `LOG_USER`、level が `LOG_INFO` で `messages` に混ざってしまうので、専用の `local6` / `debug` に振る。

```sh
# yum install gcc make
# cd /usr/local/src
# curl -O https://ftp.gnu.org/gnu/bash/bash-4.4.18.tar.gz
# tar xvzf bash-4.4.18.tar.gz
# cd bash-4.4.18
# cp -p config-top.h config-top.h.bak
# vi config-top.h
```

```diff
+ #define SYSLOG_HISTORY
- #  define SYSLOG_FACILITY LOG_USER
- #  define SYSLOG_LEVEL LOG_INFO
+ #  define SYSLOG_FACILITY LOG_LOCAL6
+ #  define SYSLOG_LEVEL LOG_DEBUG
```

```sh
# ./configure
# make
# make install       # /usr/local/bin/bash に入る
# /usr/local/bin/bash --version
```

## 2. rsyslog

```conf
# It is a rule to save the HISTORY of BASH.
local6.debug /var/log/history.log
```

を `/etc/rsyslog.conf` に足し、ファイルを `600` で作ってから再起動する。

```sh
# touch /var/log/history.log
# chmod 600 /var/log/history.log
# systemctl restart rsyslog
```

新しい bash を起動してコマンドを打つと、次の形式で残る。

```text
Sep 26 09:18:25 localhost /usr/local/bin/bash[3161]: HISTORY: PID=3161 UID=0 echo "test"
```

## 3. ログインシェルの切り替え

`/etc/shells` に `/usr/local/bin/bash` を追加し、`chsh` で切り替える。

```sh
# cp -p /etc/shells /etc/shells.bak
# echo /usr/local/bin/bash >> /etc/shells
# chsh -s /usr/local/bin/bash root
```

対象は `/etc/passwd` から `nologin` を除いて確認する。`sync`・`shutdown`・`halt` のようにログインシェルに専用コマンドが指定されているユーザーは、切り替え対象にしない。

## 4. logrotate

`/etc/logrotate.d/syslog` の対象リストに `/var/log/history.log` を足す。足したあとは `logrotate -dv /etc/logrotate.conf`（-d は実際には回さない dry run）で、履歴ログが対象に入っていることを確認する。
