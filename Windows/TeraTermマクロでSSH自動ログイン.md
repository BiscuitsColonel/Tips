# Tera Term マクロで SSH に自動ログインする（パスワード認証・鍵認証・踏み台経由）

Tera Term のマクロ（`.ttl`）で、接続コマンドの文字列を組み立てて SSH 接続し、ログイン後に `su -` までを自動化する3パターン。サーバー・ユーザー・パスワードは載せない。

（2020-02 〜 2020-11 時点のメモ。参考にした記事の URL は末尾）

## 共通の考え方

`connect` に渡す文字列を `strconcat` で組み立てる。ホスト、ポート、認証方式、ユーザー、パスワード（または鍵ファイル）を連結する。

## 1. パスワード認証

```text
username = '<user>'
hostname = '192.0.2.21'
userpasswd = '<password>'

msg = hostname
strconcat msg ':22 /ssh /auth=password /user='
strconcat msg username
strconcat msg ' /passwd='
strconcat msg userpasswd

connect msg

wait '@'
sendln 'sudo pwd'
wait ':'
sendln userpasswd
```

ログイン後は、プロンプトの記号（`@`、`:`）を `wait` で待ってから `sendln` で入力する。

## 2. 鍵認証 + `su - root`

```text
username = '<user>'
keyfile = '"C:\Users\<name>\.ssh\id_rsa"'
hostname = '192.0.2.60'

msg = hostname
strconcat msg ':2222 /ssh2 /auth=publickey /user='
strconcat msg username
strconcat msg ' /keyfile='
strconcat msg keyfile

connect msg

wait '<user>'
sendln 'su - root'
wait 'パスワード'
sendln '<root password>'
```

鍵ファイルのパスは、シングルクォートの中にダブルクォートを含めた文字列（上の `keyfile` の値）にして `/keyfile=` に連結していた。

## 3. 踏み台経由で2段ログインする

踏み台のログイン画面がプロンプトを出す方式のとき、1段目は `/auth=password` で接続し、2段目は踏み台のプロンプトに応答して進める。接続先ごとの違いは、変数にまとめておく。

```text
hostname1 = '192.0.2.36'
username1 = '<user1>'
password1 = '<password1>'

hostname2 = '192.0.2.21'
username2 = 'root'
password2 = '<password2>'

remote_prompt21 = 'CONNECT ->'
remote_prompt22 = 'Username:'
remote_prompt23 = 'password:'

IniFile = '"C:\Program Files (x86)\teraterm\TERATERM_RED.INI"'

msg = hostname1
strconcat msg ':22 /ssh /auth=password /user='
strconcat msg username1
strconcat msg ' /passwd='
strconcat msg password1
strconcat msg ' /F='
strconcat msg IniFile

connect msg

wait remote_prompt21
sendln hostname2

wait remote_prompt22
sendln username2

wait remote_prompt23
sendln password2
```

- `/F=` で Tera Term の設定ファイル（INI）を指定している。接続先ごとに別の INI を渡せる
- マクロの先頭にパスワードを直接書く構成のため、このファイルは共有しない。リポジトリに置かない

## 参考

- Tera Term マクロ（自動ログイン）: https://qiita.com/clustfe/items/e873f2216724fd7b96fc
- Tera Term で複数台のホストに一度にコマンドを実行する: https://orebibou.com/2014/07/teraterm%E3%81%A7%E8%A4%87%E6%95%B0%E5%8F%B0%E3%81%AE%E3%83%9B%E3%82%B9%E3%83%88%E3%81%AB%E5%AF%BE%E3%81%97%E4%B8%80%E5%BA%A6%E3%81%AB%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89%E3%82%92%E5%AE%9F%E8%A1%8C/
- 設定ファイルを読み込ませてログ出力する: https://itsakura.com/teraterm-log
