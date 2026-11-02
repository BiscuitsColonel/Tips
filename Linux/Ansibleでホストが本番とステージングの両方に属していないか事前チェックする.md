# Ansible のインベントリで、ホストが STAGING か PRODUCTION のどちらか一方だけに属しているか事前チェックする

環境別のグループ（ここでは `STAGING` と `PRODUCTION`）にホストを振り分けているインベントリで、「どちらにも属さないホスト」と「両方に属するホスト」を playbook の実行前に見つけるチェック。環境別のテンプレートを選ぶ変数（`host_group` など）がホストごとに1つに決まる前提のときに有効。

（2021-10 時点のメモ。`localhost` を対象にした playbook に role として入れ、他の playbook より先に `import_playbook` で呼んでいた）

```yaml
- name: Whether it belongs to either STAGING or PRODUCTION
  debug:
    msg: "{{ item }} does not belong to either STAGING or PRODUCTION!"
  with_items:
    - "{{ groups.all | difference((groups.STAGING + groups.PRODUCTION)) }}"
  failed_when:
    - item != ""

- name: Whether it belongs to both STAGING and PRODUCTION
  debug:
    msg: "{{ item }} belongs to both STAGING and PRODUCTION!"
  with_items:
    - "{{ groups.STAGING | intersect(groups.PRODUCTION) }}"
  failed_when:
    - item != ""
```

- `difference` で「全ホスト − (STAGING + PRODUCTION)」を取り、空でなければ失敗にする。結果が空のリストなら `with_items` のループが回らないので、そのまま通る
- `intersect` で2グループの共通要素を取り、空でなければ失敗にする
- 実行は `hosts: localhost` で1回だけ。ホスト数ぶん繰り返さないので、インベントリ全体の検査に向く
