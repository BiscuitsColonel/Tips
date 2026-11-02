# VirtualBox + Vagrant で CentOS 6/7 の検証 VM を複数台立てる Vagrantfile の構成

DB のバージョン違いやクラスタ構成を試すために、1 つの Vagrantfile に VM を 7〜11 台まとめて定義していた構成のまとめ。コード全体や初期設定スクリプトは置かず、設計の勘所と、踏んだ点だけ残す。

（2020-02 〜 2021-07 時点のメモ。VirtualBox + Vagrant、box は `centos/6` と `centos/7`。CentOS 6/7 の更新終了日は [古いOSのパッケージ管理トラブル対処](../Linux/古いOSのパッケージ管理トラブル対処.md) を参照）

## 何をするものか

`vagrant up vm1` のように VM を名前で指定して起動する。VM ごとにホスト名・box・IP を定義する。ホスト名は DB のバージョンを表すもの（`pg96`、`pg10`、`pg11`、`pg12`）と、検証用の連番（`test01`〜`test11`）だった。

## 使っていたプラグイン

```sh
vagrant plugin install vagrant-vbguest
vagrant plugin install vagrant-proxyconf
vagrant plugin install vagrant-reload
vagrant plugin install vagrant-hosts
vagrant plugin install vagrant-disksize
vagrant plugin update vagrant-vbguest
```

社内プロキシ配下では、先に環境変数（`http_proxy` / `https_proxy`）を設定してからプラグインを入れる。初期設定スクリプト側にもプロキシの設定が要る。

## 肝の設定

- 1 台に 2 つのネットワークを持たせる。`private_network` はホストと VM、VM 同士の通信用。もう 1 つは、ホストの LAN 側に出す `public_network`（`bridge:` と固定 IP を指定）か、`private_network` をもう 1 つ追加した構成のどちらかで作っていた
- SSH のポートフォワードは `guest: 22` を各 VM に定義し、ホスト側ポートは `auto_correct: true` にする。全 VM が同じホストポート（例では `33011` と `33012`）を指定していても、衝突したぶんは空いているポートへ自動でずれる。`usable_port_range` でずらす範囲を絞っておく
- 追加ディスクは `vb.customize ['createhd', ...]` で VDI を作り、`storageattach` で IDE に繋ぐ。ファイルの有無を見て、作成を一度だけにする

```ruby
config.vm.define :vm5 do |vm5|
  vm5.vm.box = "centos/7"
  vm5.vm.provider "virtualbox" do |vb|
    disk_file = "./tmp/disk1.vdi"
    unless File.exists?(disk_file)
      vb.customize ['createhd', '--filename', disk_file, '--format', 'VDI', '--size', 50 * 1024]
    end
    vb.customize ['storageattach', :id, '--storagectl', 'IDE', '--port', 1, '--device', 0, '--type', 'hdd', '--medium', disk_file]
  end
  vm5.vm.network "private_network", ip: "192.168.56.105"
  vm5.vm.hostname = "node1"
  vm5.vm.provision :hosts, :sync_hosts => true
  vm5.vm.provision :shell, privileged: true, :path => "bootstrapped.sh"
  vm5.vm.provision :reload
end
```

- `provision :hosts, :sync_hosts => true` は `vagrant-hosts` の機能で、VM 同士のホスト名解決を `/etc/hosts` に揃える。`provision :reload` は `vagrant-reload` で、シェルのプロビジョニングのあとに再起動する（SELinux の無効化などを反映するため）
- 大きなディスクを持たせる VM は `vm.disksize.size = '140GB'` を使う（`vagrant-disksize` が必要）

## 初期設定スクリプトの型（bootstrapped.sh）

OS ごと（CentOS 6 / 7 / Ubuntu）に分けた共通スクリプトで、次の順に処理する。

```sh
#!/bin/bash

# Exit if already bootstrapped
test -f /etc/bootstrapped && exit

# タイムゾーンとロケール、ファイアウォール停止、SELinux 無効化
# 共有ストレージのマウント（fstab への追記）
# 公開鍵の登録
# パッケージ更新

## stamp first bootstrap run
date > /etc/bootstrapped
```

- 先頭でスタンプファイル（`/etc/bootstrapped`）の有無を見て、`vagrant reload` や `vagrant provision` を何度叩いても一度しか実行されないようにする
- CentOS 7 用は、各コマンドの後ろに `|| exit <番号>` を付け、どの手順で失敗したかを終了コードで区別できるようにしていた（Vagrant が失敗したプロビジョニングの終了コードを出すため）
- CentOS 6 では、ロケールを `ja_JP.utf8` に替えたあとに `yum reinstall -y glibc glibc-common` を実行して反映させていた
- このスクリプトには、共有ストレージの資格情報と SSH 鍵が直接書かれていた。リポジトリに置く前に外し、外部から渡す形にすること

## Vagrant Share で VM を外部に公開する

`vagrant share` で、HTTP サーバーを立てた VM をインターネット経由で見せられる（Vagrant Cloud のアカウントが要る）。次のエラーが出たら、原因は次のいずれかだった。

```text
Vagrant was unable to detect an HTTP port for your machine.
```

- VM 内で HTTP サーバーが起動していない
- `80` 番ポートのフォワードが設定されていない（`config.vm.network "forwarded_port", guest: 80, host: 50000` のように定義する）
- VM の firewall（iptables など）で HTTP サーバーに届かない

HTTP 以外（SSH）を共有するときは `vagrant share --ssh` を使う。共有名とパスワードが払い出され、受け取った側が `vagrant connect --ssh <共有名>` で接続する。

## ngrok の追加

HTTP の Vagrant Share を試すときに、`vagrant-share` プラグインと `ngrok` を入れた。ngrok の実行ファイルは、PATH の通った場所に置く。
