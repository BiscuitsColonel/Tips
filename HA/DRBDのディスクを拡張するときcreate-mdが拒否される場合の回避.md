# DRBD の下の LVM を拡張したあと create-md が「Device size would be truncated」で拒否されるときの回避

DRBD の下のボリュームを LVM で拡張したあと、内部メタデータを新しい末尾へ移すための `drbdadm create-md` が拒否されたときに、メタデータをダンプして書き換え、`restore-md` で戻して通した記録。

（2020-02 時点のメモ。DRBD のメタデータ形式は v09、ファイルシステムは XFS。）

## 流れ

リソース名は `r0`、デバイスは `/dev/vg0/lv0` とする。

```sh
drbdadm down r0
drbdadm dump-md r0 > /tmp/metadata
```

`dump-md` が `Found meta data is "unclean", please apply-al first` で止まったら、`drbdadm apply-al r0` を実行してからダンプし直す。

LVM を拡張する。

```sh
pvcreate /dev/sdc1
vgextend vg0 /dev/sdc1
lvextend -l +100%FREE /dev/vg0/lv0
```

拡張後のサイズ（セクタ数）を取り、ダンプの `la-size-sect` をその値に書き換える。

```sh
blockdev --getsize /dev/vg0/lv0     # 例: 20946944
vi /tmp/metadata                    # la-size-sect 20946944;
```

## 拒否される

この状態で `create-md` を実行すると、確認に `yes` と答えても次のように拒否される（終了コード 40）。

```text
# drbdadm create-md r0
Move internal meta data from last-known position?
[need to type 'yes' to confirm] yes
Device size would be truncated, which
would corrupt data and result in
'access beyond end of device' errors.
You need to either
   * use external meta data (recommended)
   * shrink that filesystem first
   * zero out the device (destroy the filesystem)
Operation refused.
```

## 回避: 書き換えたダンプを restore-md で戻す

`drbdadm -d dump-md r0` が実際に組み立てる `drbdmeta` コマンドを表示するので、その `dump-md` を `restore-md` に置き換えて、書き換えたファイルを渡す。

```sh
drbdmeta_cmd=$(drbdadm -d dump-md r0)
${drbdmeta_cmd/dump-md/restore-md} /tmp/metadata
# Valid meta-data in place, overwrite? [yes]
# Do you want to proceed? [yes]
# la-size-sect was too big (20946944), truncated (20946232)!
# Successfully restored meta data
```

`truncated` と出るのは、内部メタデータが末尾に取る分（この例では 712 セクタ）を差し引いた値に自動で丸められたため。ここで成功する。

そのあと上げ直して、ファイルシステムを広げる。

```sh
drbdadm up r0
drbdadm primary r0
mount /dev/drbd1 /mnt/drbd
xfs_growfs /dev/drbd1
df -h
```

元メモには、これを両ノードで行うか、片ノードの拡張後に再同期させるかの記載がない。実施するときは構成に合わせて確認すること。
