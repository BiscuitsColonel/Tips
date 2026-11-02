# EOL した CentOS の yum 復旧・旧バージョン導入と、Ubuntu の dpkg 上書きエラー対処

古い CentOS を検証用に動かすときの yum まわりの障害と、Ubuntu で `apt upgrade` が dpkg のエラーで止まったときの対処。

（2020-09 〜 2021-05 時点のメモ。CentOS 6/7 と Ubuntu で検証。CentOS 6 は 2020-11-30、CentOS 7 は 2024-06-30 に更新が終了している。出典: [CentOS Linux](https://www.centos.org/centos-linux/)、[FAQ: CentOS Stream Updates](https://www.redhat.com/en/blog/faq-centos-stream-updates)）

## CentOS: yum が `Cannot find a valid baseurl for repo: base` で失敗する

Vagrant の `yum install` や `vagrant up` のプロビジョニングが、次のエラーで止まる。ミラーリストの URL が古いバージョンを返さなくなったのが原因なので、リポジトリを vault に向ける。

```text
YumRepo Error: All mirror URLs are not using ftp, http[s] or file.
 Eg. Invalid release/repo/arch combination/
Error: Cannot find a valid baseurl for repo: base
```

```sh
# sed -i -e "s/^mirrorlist=http:\/\/mirrorlist.centos.org/#mirrorlist=http:\/\/mirrorlist.centos.org/g" /etc/yum.repos.d/CentOS-Base.repo
# sed -i -e "s/^#baseurl=http:\/\/mirror.centos.org/baseurl=http:\/\/vault.centos.org/g" /etc/yum.repos.d/CentOS-Base.repo
# yum clean all
```

### その後、https の RPM 取得が `SSL connect error (35)` で失敗する

yum 自体は通るようになっても、`rpm -ivh https://...` が TLS ハンドシェイクで失敗する（curl の `NSS error -12190`、`Error in TLS handshake, trying SSLv3...`）。古い OS 同梱の NSS が現在の TLS に付いていけないのが原因で、yum で NSS を更新すると直る。

```sh
# yum update -y nss
```

## CentOS: 公式サイトにない旧バージョンを入れる

公式のダウンロードページには最新版しか置かれていないので、旧バージョンの ISO は vault.centos.org から取る（`http://vault.centos.org/<バージョン>/os/x86_64/`）。ネットワークインストール用の ISO を使う場合は、インストールソースの URL にも同じ vault の URL を入力する。

## CentOS 7.5 を 7.4 にダウングレードする

バージョンアップ直後の環境なら、`releasever` と参照リポジトリを vault に向けて `distribution-synchronization` でダウングレードできる。マイナーバージョンのダウングレードは可能だが、メジャーバージョンのダウングレード（7 → 6 など）はできない。

systemd は削除保護がかかっていて、そのままではダウングレードの途中で失敗する。先に保護用の設定ファイルを退避する。

```sh
# echo 7.4.1708 > /etc/yum/vars/releasever
# sed -i".org" -e "s/^mirror/#mirror/" \
               -e "s/^#baseurl/baseurl/g" \
               -e "s/mirror.centos/vault.centos/g" \
               /etc/yum.repos.d/CentOS-Base.repo
# mv /etc/yum/protected.d/systemd.conf /etc/yum/protected.d/systemd.conf.bak
# yum clean all
# yum distribution-synchronization
# cat /etc/redhat-release
CentOS Linux release 7.4.1708 (Core)
```

完了後に OS を再起動して、バージョンが変わっていることを確認する。

## Ubuntu: `apt upgrade` が dpkg の展開エラーで止まる

パッケージの展開中に、別パッケージが持つファイルを上書きしようとして dpkg が失敗することがある（例では `flat-remix` のアイコンファイルが `Not allowed to overwrite` 扱いになった）。

```text
dpkg: error processing archive /var/cache/apt/archives/flat-remix_20190908_amd64.deb (--unpack):
 ...
E: Sub-process /usr/bin/dpkg returned an error code (1)
```

エラーになった `.deb` を指定して、強制上書きで入れ直すと解消した。

```sh
$ sudo dpkg -i --force-overwrite /var/cache/apt/archives/flat-remix_20190908_amd64.deb
```

今回はアイコンセットだったので上書きで問題ないと判断した。システムに関わるパッケージで同じエラーが出たら、強制上書きの前に、衝突しているファイルの持ち主を調べる。上書きしても直らない場合は、該当パッケージを一度削除して入れ直す。

```sh
$ sudo dpkg -P flat-remix
```
