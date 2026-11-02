# DB サーバーのバックアップ先に CIFS/NFS 共有をマウントするときの勘所（マウント先の作り方と UID/GID の揃え方）

バックアップ先の共有ストレージを `/etc/fstab` でマウントするときに、事故を防ぐために決めていた手順。接続先のホスト名・IP・ユーザー名・パスワードは載せない。

（2020-02 〜 2020-09 時点のメモ。RHEL 系の OS）

## 手順と、順序に依存する点

1. 事前に、接続先へ `ping` が通ることと `df -h` を確認する
2. `fstab` を日付付きでバックアップしてから編集する（`cp /etc/fstab /etc/fstab_<日付>`）。編集後は `diff` で意図した行だけが増えたことを確認する
3. マウント先のディレクトリは root で作る。マウントされていない間は、アプリのユーザー（例では `postgres`）が書き込めないようにするため。マウントしていない状態でバックアップが走っても、ローカルディスクに書かれずに失敗する
4. `mount <マウント先>` で実際にマウントし、`df -h` で容量が見えることを確認してから、必要なら `umount` で戻す

```text
//<host>/<share> /mnt/backup cifs username=<user>,password=<password>,sec=ntlm,uid=postgres,gid=postgres,dir_mode=0700,file_mode=0644 0 0
```

`uid`/`gid` と `dir_mode`/`file_mode` を付けて、マウント先のファイルをアプリのユーザーだけが触れるようにしていた。

## NFS を使うときは UID/GID をサーバー間で揃える

NFS では権限がサーバー間でずれないように、DB ユーザー（`postgres`）の UID/GID を全サーバーで同じ値に固定して作る。値は環境ごとに決める（`61001` のように、自動採番の範囲 `UID_MIN`〜`UID_MAX`（`/etc/login.defs` で確認。既定は 1000〜60000）の外の数字を指定する）。

```sh
# groupadd -g <gid> postgres
# useradd -u <uid> -g <gid> -m postgres
```

`-u`/`-g` を省略すると、サーバーごとに既存の ID の続きが採番されて、揃わなくなる。
