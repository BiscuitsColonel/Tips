# Ubuntu・CentOS 7 のデスクトップへ VNC で接続するときの暗号化エラーと再起動時の対処

サーバーに GUI を入れて VNC で操作するときに、クライアントが繋がらない・接続が切れる問題の回避策。

（2021-09 〜 2021-10 時点のメモ。Ubuntu デスクトップ、CentOS 7 で検証）

## Ubuntu: Windows/Mac の VNC クライアントから繋がらない

Ubuntu の Vino（画面共有）は暗号化通信を要求する。Windows や Mac の VNC クライアントは暗号化に対応していないものが多く、設定を合わせても接続エラーになる。Ubuntu 側で暗号化の要求を切ると繋がる。

```sh
$ gsettings set org.gnome.Vino require-encryption false
```

`gsettings` が通らないときは、`DISPLAY` を付けて実行する。

```sh
$ DISPLAY=:0 gsettings set org.gnome.Vino require-encryption false
```

設定は「設定 > 共有 > 画面共有」を ON にし、アクセスオプションでパスワードを要求する形にしておく。

### Enter キーで接続が切れ、再接続すると画面が真っ黒になる

VNC 接続中に Enter を押すと接続が切れ、再接続するとログイン後の画面ではなくなって、黒い画面になる。本体側がログイン画面に戻ってしまっているのが原因。別の PC から SSH で入り、ディスプレイマネージャーを再起動する。

```sh
$ sudo service lightdm restart
```

lightdm は `sudo apt -y install lightdm` で入れて切り替えたものを使っている。

### Vino の代わりに x11vnc を systemd で常駐させる

```sh
$ sudo apt -y install x11vnc
$ sudo x11vnc -storepasswd /etc/x11vnc.passwd
$ sudo chmod 600 /etc/x11vnc.passwd
```

`/etc/systemd/system/x11vnc.service` を次の内容で作る。

```ini
[Unit]
Description=x11vnc (Remote access)
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/x11vnc -auth guess -display :0 -rfbauth /etc/x11vnc.passwd -rfbport 5900 -forever -loop -noxdamage -repeat -shared
ExecStop=/bin/kill -TERM $MAINPID
ExecReload=/bin/kill -HUP $MAINPID
KillMode=control-group
Restart=on-failure

[Install]
WantedBy=graphical.target
```

```sh
$ sudo systemctl daemon-reload
$ sudo systemctl enable x11vnc
$ sudo systemctl start x11vnc
```

`-auth guess` は、ログイン画面の前から X の認証情報を探して繋ぐための指定。

## CentOS 7: GNOME と xrdp / TigerVNC

```sh
# yum update grub2-common -y
# yum install fwupdate-efi -y
# yum groupinstall graphical-server-environment -y
# yum install xrdp tigervnc-server mesa-libEGL -y
# systemctl enable --now xrdp
# systemctl set-default graphical.target
# reboot
```

TigerVNC はユーザーごとのユニットを作る。テンプレートの `vncserver@.service` をコピーし、行 32 と 50 にある `<USER>` を使うユーザー名に置換する。

```sh
# cp /usr/lib/systemd/system/vncserver@.service /etc/systemd/system/vncserver-<user>@.service
# sed -i -e '32,50 s/<USER>/<user>/' /etc/systemd/system/vncserver-<user>@.service
# su - <user>
$ vncpasswd    # view-only password は n
$ exit
# systemctl daemon-reload
# systemctl --now enable vncserver-<user>@:1
```

接続先は VNC のポート 5900 台（ディスプレイ :1 なら 5901）。GNOME の color-manager が毎回認証を求めてくるのを避けたい場合は、polkit のルールで `org.freedesktop.color-manager.*` のアクションを許可する（`/etc/polkit-1/rules.d/` に置く）。

CentOS 7 も Vino を使う場合は、Ubuntu と同じ暗号化の無効化が必要になる。

```sh
$ DISPLAY=:0 gsettings set org.gnome.Vino require-encryption false
```
