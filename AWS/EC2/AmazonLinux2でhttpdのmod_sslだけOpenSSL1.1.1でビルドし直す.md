# Amazon Linux 2 で OpenSSL 1.1.1 を自前ビルドし、httpd の mod_ssl だけを作り直して差し替える

標準の OpenSSL では足りない機能が必要なときに、OS 標準の httpd はそのままにして、`mod_ssl.so` だけを自前の OpenSSL にリンクして入れ替える userdata の流れ。順序に依存する点を残す。

（2022-01 時点のメモ。Amazon Linux 2 の userdata として実際に使っていたスクリプトの要点）

## 流れ

1. 開発系パッケージを入れる（`gcc` `gcc-c++` `httpd-devel` `apr-devel` `apr-util-devel` `pcre-devel` `zlib-devel` など）
2. OpenSSL 1.1.1 のソースを取得し、共有ライブラリとしてビルドして入れる
3. 入れ先のライブラリパスを `ld.so.conf.d` に登録して `ldconfig` する
4. 稼働中の httpd と同じバージョンのソースを取得し、`--with-ssl` を指定して `mod_ssl` だけをビルドする
5. できた `mod_ssl.so` を `/etc/httpd/modules/` にコピーして httpd を再起動する

```sh
# 2-3. OpenSSL（デフォルトの prefix は /usr/local）
./config shared zlib
make depend && make && make install
echo /usr/local/lib64 > /etc/ld.so.conf.d/openssl111.conf && ldconfig

# 4-5. httpd は「インストール済みの httpd -v と同じ版」のソースを取る
VER=$(httpd -v | grep -o "version: .*[0-9.]" | tr -cd '0123456789.\n')
wget https://archive.apache.org/dist/httpd/httpd-${VER}.tar.gz
tar xf httpd-${VER}.tar.gz && cd httpd-${VER}
./configure --with-ssl=/usr/local/lib64
make && cp modules/ssl/.libs/mod_ssl.so /etc/httpd/modules/
```

## 勘所

- httpd のソースは最新ではなく、`httpd -v` で得たバージョンに合わせて取得している
- 同じ userdata の中で、PHP は `amazon-linux-extras` で入れ（7.3 を指定）、Passenger は Ruby を `amazon-linux-extras` で入れてから `gem install passenger` + `passenger-install-apache2-module` で入れている。`passenger-install-apache2-module` は対話があるため `yes |` で流す
- LDAP 認証が要るなら `mod_ldap` は `yum` で入る。`X-Forwarded-For` を信頼したい場合の `mod_extract_forwarded` は yum ではなく GitHub のソースから `apxs -c -i -a` でビルドして入れている
- `ldconfig` は OpenSSL を入れた直後、httpd をビルドする前に実行している

この手順は、メモに残っていたスクリプトの要点を整理したもので、`--with-ssl` に渡すパスの妥当性までは再検証していない。
