# Tips

## Intent

少しググっただけでは見つけにくい IT の知識を、あとで自分が読み返して使える形でメモする。

## 構成

- `{カテゴリ}/[{サブカテゴリ}/]{トピック}.md` — 1トピック1ファイル。カテゴリは英語、ファイル名は日本語でよい
- 画像は各カテゴリの `img/` に置く
- `IDE/Eclipse/xml/` のように、取り込んで使う設定ファイルはそのまま置いてよい
- `README.md` は `scripts/gen-readme.py` が各 md の1行目から生成する。手で編集しない

## ルール

- 残す基準・書き方・載せてはいけない情報: [.claude/rules/writing.md](.claude/rules/writing.md)
- 外部のメモ（Google Drive など）をまとめて取り込む・既存の Tip を整理し直す手順: [.claude/skills/import-tips/SKILL.md](.claude/skills/import-tips/SKILL.md)
- 追加・変更したら `python scripts/check-tips.py` を通す
- public リポジトリなので、clone したら最初に `git config core.hooksPath .githooks` を実行する。検査に通らないコミットを pre-commit hook が止める。`git config core.hooksPath` の出力が `.githooks` でなければ、作業の前に設定する
