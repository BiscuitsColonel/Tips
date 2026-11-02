# Pacemaker の切り替え操作で制約が残る問題と、fail-count・cleanup の扱い

Pacemaker のリソースを手で動かすときの落とし穴。`move` は移動後も制約を残し、`cleanup` はリソースを再起動する。切り替え試験の観点も合わせて残す。

（2020-03〜2021-11 時点のメモ。CentOS 7 同梱の Pacemaker 1.1.x。fail-count の挙動は元メモの書き手の注釈で、検証ログは付いていない。）

## move は制約を残す

`crm resource move` / `pcs resource move` は、リソースを移せても「元のノードでは動かさない」制約を残す。消し忘れると、障害時にフェイルオーバーされない。`crm` では `crm configure show` を見ないと、この制約に気付けない。

```sh
pcs resource move <resource> <node>
pcs constraint location show
#   Enabled on: <node> (score:INFINITY)
#   Disabled on: <other> (score:-INFINITY)
pcs resource clear <resource>     # 制約を解除
```

そのため、クラスタの切り替え操作は `move` ではなく、ノードの standby / online で行う。

```sh
crm node standby <node>
crm node online  <node>
```

standby にしたノードは Primary にならない。standby にしたら必ず online に戻す。

## fail-count の挙動（元メモの記載）

`crm_mon -rfo` で見たときの注釈として、次のように書いていた。

- リソースが故障して再起動に成功すると、fail-count が加算される
- 起動（start）に失敗した場合は、fail-count が INFINITY になり、そのノードでは起動を試みず即時フェイルオーバーされる（既定の `start-failure-is-fatal=true` のとき。[Pacemaker Explained: Cluster-Wide Configuration Options](https://clusterlabs.org/projects/pacemaker/doc/2.1/Pacemaker_Explained/html/cluster-options.html) は、起動の失敗がそのノードでの以降の起動を妨げるとしている）
- fail-count が `migration-threshold`（2 に設定）以上なら、再起動に関係なく即時フェイルオーバーされる

クリアの方法は 2 つある。

| コマンド | 何が消えるか |
| --- | --- |
| `crm_failcount -D -r <resource>` | fail-count だけ |
| `crm resource cleanup <resource> <node>`（`pcs resource cleanup`） | fail-count と故障履歴。消したあとにリソースの状態が再評価され、状態によっては再起動される（必ず再起動されるとは限らない） |

`cleanup` は状態の再評価で再起動を伴うことがあるので、稼働中のリソースに安易に打たない。

## スプリットブレインが起きないかを見る試験の設計

片側のノードの NIC の IP アドレスを変えて通信断を作り、スプリットブレインが起きないかを確認する。

- 変更する側へは、変更対象とは別の IP で接続する
- Primary 側の IP を変えなかった場合の期待: Primary は無影響で、変更したスタンバイ側の Pacemaker だけが停止する
- Primary 側の IP を変えた場合の期待: Primary が切り替わり、元の Primary の Pacemaker が停止する
- 切り替わった先で DB に接続して `SELECT` できるところまで確認する
- IP が複数ある構成では、すべての IP について 1 つずつ試す
- 戻したあとは `ping` が通ることを確認する

これは確認項目で、実測値の記録ではない。
