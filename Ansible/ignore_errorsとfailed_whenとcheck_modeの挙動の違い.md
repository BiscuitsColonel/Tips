# Ansible の ignore_errors・failed_when・check_mode・Gathering Facts を実際に動かして確かめた挙動

エラーを無視する書き方による `PLAY RECAP` の数え方の違い、`--check` で実行されないタスクの扱い、Gathering Facts が失敗する条件。

（2021-11 時点のメモ。）

## PLAY RECAP の数え方

必ず失敗する `/bin/false` に、書き方を変えて付けて実行した結果。

| 書き方 | RECAP |
| --- | --- |
| `ignore_errors: yes` | `ok=1 ignored=1`（ignored に数えられる） |
| `failed_when: no` | `ok=1 ignored=0`（成功として数えられる） |
| `changed_when: no` | 失敗のまま（`failed=1`）。`changed` の表示だけが変わる |

`changed_when` は changed と報告するかどうかの判定で、失敗の判定には関わらない。失敗を無視したいなら `ignore_errors` か `failed_when` を使う（[公式: Error handling in playbooks](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_error_handling.html)）。なお `command` / `shell` は、何もしなくても既定で changed と報告するので、冪等にしたいときは `changed_when` や `creates` / `removes` で制御する。

失敗したことを記録に残したいなら `ignore_errors`、最初から失敗ではない扱いにしたいなら `failed_when` を使う。

`block` / `rescue` は try〜catch に近い。エラーが出ても全体を強制終了せず、`rescue` に進んで続行できる。

## check_mode

- `check_mode: yes` は、`--check` を付けなくても常に dry run になる
- `check_mode: no` は、`--check` を付けても通常どおり実行される。2.2 で非推奨になった `always_run` の代わり（[公式: Validating tasks: check mode and diff mode](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_checkmode.html)）
- `no` にしたタスクは本当に実行されるので、事故が起きないか確認して使う

`shell` / `command` は、`creates` / `removes` を指定しないと check モードではスキップされて実行されない（[command モジュール](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html)の check mode は partial）。そのため、`shell` の結果を使うタスクは `--check` で検証できない。結果を使うタスクだけ `check_mode: no` にして、実際の結果を得る。

`--syntax-check` は構文チェックだけ。実行はしない。

## Gathering Facts

対象ホストの `/etc/sudoers` にわざと typo を入れて playbook を流すと、エラーは最初の Gathering Facts（setup モジュール）で出る。`setup` を手で実行しても同じエラーになる。ただしこれは、fact 収集に `become`（sudo）が効いている場合の話。`become` を使わない play なら、sudoers の壊れは Gathering Facts では出ず、最初の `become` するタスクで出る。

- 速度を優先するなら `gather_facts: no`
- タスク内で `become: yes` によりユーザを切り替えても、取得済みの fact は切り替え前のユーザのまま更新されない。更新したいなら、`gather_facts` のタスクを改めて置く
