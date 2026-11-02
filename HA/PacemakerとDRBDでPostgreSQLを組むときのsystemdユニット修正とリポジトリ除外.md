# Pacemaker + DRBD + PostgreSQL（CentOS 7）で先にやっておく systemd 修正とリポジトリ除外

Linux-HA Japan のリポジトリで Pacemaker を入れ、DRBD（内部メタデータ）のうえに PostgreSQL を載せる 2 ノード構成で、公式手順だけでは見落としやすい設定。

（2021-11 時点のメモ。CentOS 7、DRBD 9.0、Pacemaker は Linux-HA Japan 版。SELinux は permissive。）

## CentOS 7 標準パッケージとの混在を避ける

`/etc/yum.repos.d/CentOS-Base.repo` の `[base]` と `[updates]` に除外を入れる。入れないと、標準リポジトリ側のバージョンが混ざって入る。

```text
exclude=pacemaker* corosync* resource-agents* crmsh* cluster-glue* libqb* fence-agents* pcs*
```

CentOS 7 だけの作業として、`NetworkManager-config-server` を入れて NetworkManager を再起動する（元メモでは RHEL では不要と書いている）。

## Pacemaker / Corosync の systemd ユニット

`/usr/lib/systemd/system/` のユニットを `/etc/systemd/system/` にコピーして編集する（パッケージ更新で上書きされないため）。

| ユニット | 設定 | 理由 |
| --- | --- | --- |
| `/etc/sysconfig/pacemaker` | `PCMK_fail_fast=yes` | Pacemaker の内部プロセスが死んだ場合もノード故障として扱う |
| `corosync.service` | `Restart=on-failure`、`RestartSec=70`、`ExecStartPre=/sbin/modprobe softdog` のコメントを外す | Corosync のプロセス故障時に watchdog を効かせる |
| `pacemaker.service` | `ExecStopPost=/bin/sh -c 'pidof crmd \|\| killall -TERM corosync'` のコメントを外す | Pacemaker が止まったら Corosync も止める |

`corosync.conf` は `transport: udpu`、`token: 30000`、`token_retransmits_before_loss_const: 10`、`join: 5000`、`secauth: off`、`two_node: 1`。

## CIB の値

- クラスタ全体: `no-quorum-policy=ignore`、`stonith-enabled=false`、`startup-fencing=false`、`pe-*-series-max=100`
- リソースの既定: `resource-stickiness=INFINITY`、`migration-threshold=2`
- VIP（IPaddr2）: monitor 5s、`on-fail=standby`
- ファイルシステム（Filesystem）: monitor 5s、`on-fail=restart`。stop は `on-fail=block`
- `pgsql`: monitor 30s、start と stop の timeout は 120
- group の順は、ファイルシステム、VIP、`pgsql`

3 ノード目を足して 1 台が OFFLINE の状態では、`pcs status` に `partition WITHOUT quorum` と出るが、`no-quorum-policy=ignore` ならリソースは Started のまま動く。

## DRBD

- 初期同期は、片側を `drbdadm primary --force` で Primary にし、`drbdsetup status --verbose --statistics` で out-of-sync が 0 になるまで待つ
- ボリュームを広げるときの `create-md` の拒否と回避は [DRBDのディスクを拡張するときcreate-mdが拒否される場合の回避.md](DRBDのディスクを拡張するときcreate-mdが拒否される場合の回避.md)

DRBD 9 のマウントは、Pacemaker の Filesystem リソースに任せて切り替える（OS 側で自動マウントしない）。
