# 自作 playbook「HAProxy + Pacemaker で冗長化した Web / SMTP 振り分け環境」の構成と順序依存

HAProxy を Pacemaker（Corosync）で Active/Standby にし、背後の nginx（Docker）2 台へ HTTP を、postfix 2 台へ SMTP を振り分ける検証環境を作る自作プロジェクト。コード全体は置かず、何をするものかと、順序や構成の要点だけを残す。

（2021-09〜10 時点のメモ。CentOS 7。）

## 構成

- role: `common`（SELinux と firewalld を無効化）、`docker`、`nginx`、`postfix`、`haproxy`、`pacemaker`
- `main.yml` が `web.yml`、`mail.yml`、`haproxy.yml` を順に `import_playbook` する
- 確認用に、nginx の `index.html` を `{{ inventory_hostname }}` だけにしておくと、どのバックエンドが応えたかが画面で分かる

## 順序依存と、落とし穴になった点

- Pacemaker を起動したあと、60 秒待つ（`pause`）。そのあとで `crm configure load update` を **`run_once: yes`** で 1 台からだけ流す
- Pacemaker は OS 起動時に自動起動させず（`enabled: false`）、HAProxy の起動は systemd のユニットではなく Pacemaker のリソースに任せる。role に HAProxy を起動するタスクは置かない
- HAProxy で SMTP（25 番）を受けるので、同居する postfix は `stopped` かつ `enabled: false` にしておく
- nginx は LB の背後でクライアントの IP を取るため、`set_real_ip_from` と `real_ip_header X-Forwarded-For` を `default.conf` に入れる

## HAProxy の設定の要点

```text
cookie SERVERID insert nocache indirect preserve maxidle 30m maxlife 8h
option httpchk GET /index.html
server Web1 {{ web_host1 }}:{{ web_port }} weight 1 inter 3000 check cookie server1
```

HTTP は cookie でセッションを固定する。SMTP は `mode tcp` にして `option smtpchk` で死活を見る。

## Pacemaker 側

```text
property no-quorum-policy="ignore" stonith-enabled="false"
rsc_defaults resource-stickiness="INFINITY" migration-threshold="2"
primitive vip ocf:heartbeat:IPaddr2 params ip="{{ pacemaker_vip }}" op monitor interval="5s"
group grp vip haproxyd
```

VIP と HAProxy を `group` にして、同じノードで上がるようにする。`corosync.conf` は 2 ノード用に `two_node: 1`、`transport: udpu`、`token: 30000`。設定値の理由は [HAProxyをPacemaker2台で冗長化しバックエンドを手動切り戻しにする設計.md](../HA/HAProxyをPacemaker2台で冗長化しバックエンドを手動切り戻しにする設計.md) にある。ただし、そちらは HAProxy 単体のリソースで monitor `interval` を 1 秒にしており、ここの VIP は 5 秒で、`group` 構成も違う。どの値がどの理由に対応するかは、元の playbook の記述。未確認。
