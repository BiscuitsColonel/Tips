# Windows のイベントログを nxlog で Linux の rsyslog に UDP 転送する

Windows サーバーのイベントログ（Application / System / Security の警告以上）を、JSON にして syslog 形式で Linux のログサーバーへ送り、専用ファイルに保存する構成。受信側（rsyslog）、送信側（nxlog）、疎通テスト、ローテートの順に書く。IP は `192.0.2.0/24` のダミー。

（2019-09 〜 2019-10 時点のメモ。受信側は RHEL 系の rsyslog、送信側は nxlog Community Edition の Windows 版）

## 1. 受信側（rsyslog）

UDP 514 を受信するようにし、送信元ごとにファイルへ振り分ける。

```conf
# /etc/rsyslog.conf
$ModLoad imudp
$UDPServerRun 514

## Remote host logging
:fromhost-ip, isequal, "192.0.2.11" /var/log/windows_event.log
:fromhost-ip, isequal, "192.0.2.12" /var/log/windows_event.log
& stop
```

`& stop` を付けて、`/var/log/messages` に二重に出ないようにする。先に保存先のファイルを `600` で作っておき、`systemctl restart rsyslog` する。

## 2. 送信側（nxlog.conf）

`C:\Program Files (x86)\nxlog\conf\nxlog.conf` を、編集前にコピーしてから次を足す。

```text
<Extension syslog>
Module xm_syslog
</Extension>

<Extension charconv>
Module xm_charconv
AutodetectCharsets shift_jis, utf-8
</Extension>

<Extension json>
Module xm_json
</Extension>

<Input in>
Module im_msvistalog
Query <QueryList>\
<Query Id="0">\
<Select Path="Application">*[System[(Level=1 or Level=2 or Level=3)]]</Select>\
<Select Path="System">*[System[(Level=1 or Level=2 or Level=3)]]</Select>\
<Select Path="Security">*[System[(Level=1 or Level=2 or Level=3)]]</Select>\
</Query>\
</QueryList>
Exec $raw_event = "json=" + to_json(); $SyslogFacilityValue = 21;
Exec convert_fields("utf-8", "utf-8");
</Input>

<Processor t>
Module pm_transformer
OutputFormat syslog_bsd
Exec $Message=(": "+$raw_event);
</Processor>

<Output out>
Module om_udp
Host 192.0.2.15
Port 514
</Output>

<Route r>
Path in => t => out
</Route>
```

- `$SyslogFacilityValue = 21` で syslog の facility を指定している
- `Level=1 or 2 or 3` のイベントだけを送り、情報レベルは送らない

Security ログを取るには、Windows 側の「ローカル セキュリティ ポリシー」で監査ポリシーを設定しておく。nxlog のサービスは「スタートアップの種類」が自動になっていることを確認して起動する。

## 3. 疎通テスト

`C:\Program Files (x86)\nxlog\data\nxlog.log` にエラーが出ていないことを確認し、コマンドプロンプトで テスト用イベントを作る。

```text
> EVENTCREATE /ID 999 /L system /SO sys_test /T WARNING /D "テストです"
```

受信側のログファイルに、そのイベントが入っていれば成功。

## 4. 受信ログのローテート

受信ファイルを `/etc/logrotate.d/syslog` の対象リストに足す。

```text
/var/log/windows_event.log
```

足したあと `logrotate -dv /etc/logrotate.conf` で、リストに入っていることを dry run で確認する。
