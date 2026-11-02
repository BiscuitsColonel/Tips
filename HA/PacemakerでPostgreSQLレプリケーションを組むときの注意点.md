# Pacemaker で PostgreSQL ストリーミングレプリケーションを組むときに外せない点と動作確認の見方

Pacemaker（`pgsql` リソースエージェント）で PostgreSQL 11 のストリーミングレプリケーションを 2 ノードで組み、前段の Pgpool-II で振り分けた構成で、ハマりどころと動作確認の観点を残す。手順そのものは公式のクラスタ構築手順に従えばよい。

（2020-08〜2021-11 時点のメモ。CentOS 7、PostgreSQL 11、Pacemaker 1.1.19（Linux-HA Japan のリポジトリ）、Pgpool-II 4.x。）

## 構築で外せない点

- スタンバイの初期化で `pg_basebackup` に `-R` を付けない。`recovery.conf` は Pacemaker が作るので、付けると食い違う

```sh
pg_basebackup -h <primary> -U rep -D $PGDATA --progress
```

- 故障したノードをクラスタへ戻す前に、ロックファイルを消す。残っていると、そのノードがマスタへ昇格できない状態のままになる

```sh
rm -f /var/lib/pgsql/tmp/PGSQL.lock
```

- Corosync の `token` は 30000 ms と長めにし、`transport: udpu` にする（理由は [HAProxyをPacemaker2台で冗長化しバックエンドを手動切り戻しにする設計.md](HAProxyをPacemaker2台で冗長化しバックエンドを手動切り戻しにする設計.md)）
- テスト環境で SSH のパスワード認証を有効にするため、`sshd_config` を `sed` で書き換えて `sshd` を再起動した。本番では鍵認証にする

## 動作確認の観点

切り替えやリカバリの試験は、毎回 `date ;` を前置きして時刻をそろえると、あとでログと突き合わせやすい。

| 確認 | コマンド |
| --- | --- |
| レプリケーションの遅れ（プライマリ） | `select pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) from pg_stat_replication;` |
| Pgpool-II のノード状態 | `psql -h <vip> -p 9999 -c "show pool_nodes"` |
| バックエンドの状態 | `pcp_node_info -h localhost -v -w 0`（ノード番号を変える） |
| Pgpool-II の Master/Standby | `pcp_watchdog_info -h <node> -w` |
| スタンバイを戻す | `pcp_recovery_node -h <vip> -p 9898 -U postgres -n <ノード番号>` |

試験の流れは次の順にした。

1. プライマリの PostgreSQL を `kill -9` し、`show pool_nodes` で切り替わりを確認する
2. 落ちたノードを `pcp_recovery_node` で戻し、`show pool_nodes` で両ノードが up であることを確認する
3. Pacemaker 側は、プライマリ側のノードを再起動して `crm_mon` で切り替わりを見る。落ちたノードは `systemctl start pacemaker` で戻す
4. 監視（Zabbix）も、PostgreSQL や Pacemaker のプライマリが変わっても追従できるか、アクティブチェックで確認する

## Pgpool-II を含めた起動停止の注意

- 両ノードが同時に急に落ちた場合、Pgpool-II と PostgreSQL は作り直しになる。Pgpool-II はそのような落ち方を想定して作られていない
- 起動・停止（落とし上げ）に失敗すると、VIP と PORT ファイルが残るので、状況に応じて削除する
