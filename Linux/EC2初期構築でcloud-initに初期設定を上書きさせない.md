# EC2（RHEL / Amazon Linux）の初期構築で、ロケール・タイムゾーン・ホスト名を cloud-init の初期化対象から外す

払い出し直後の EC2 に、ロケールとタイムゾーンとホスト名を設定するときの手順。cloud-init の初期化処理の対象から、ロケール・タイムゾーン・ホスト名を外しておく。

（2021-11 時点のメモ。RHEL と Amazon Linux で使った手順）

`/etc/cloud/cloud.cfg` の初期化モジュールの一覧から `locale` と `timezone` を外し、ホスト名は `preserve_hostname: true` で固定する。

```sh
# sed -i -e 's/ - locale/# - locale/g' -e 's/ - timezone/# - timezone/g' /etc/cloud/cloud.cfg
# echo "preserve_hostname: true" >> /etc/cloud/cloud.cfg
```

## ディストリビューションごとの違い（同じ手順でも設定先が違うもの）

| 項目 | RHEL | Amazon Linux |
| --- | --- | --- |
| タイムゾーン | `timedatectl set-time-zone Asia/Tokyo` | `ln -sf /usr/share/zoneinfo/Japan /etc/localtime` と `/etc/sysconfig/clock` の `ZONE` を書き換え |
| ロケール | `yum install glibc-langpack-ja` のあと `localectl set-locale LANG=ja_JP.utf8` | `/etc/sysconfig/i18n` の `LANG` を書き換え |

タイムゾーンを変えたあとは `systemctl restart crond` で cron にも反映させる。

## 時刻同期（Amazon Time Sync Service）

EC2 から使える NTP サーバー `169.254.169.123` を `chrony` に指定する。

```sh
# sed -i -e 's/^server.*/server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4/g' /etc/chrony.conf
# systemctl restart chronyd
```

## ほかに気をつける点

- Amazon Linux は、`yum update` を実行した時点の最新リリースにパッケージが更新される（リリースを固定する必要はない）
- RHEL では、意図しないマイナーバージョンアップを避けるなら `/etc/yum.conf` に `exclude=redhat-release*` を足す
