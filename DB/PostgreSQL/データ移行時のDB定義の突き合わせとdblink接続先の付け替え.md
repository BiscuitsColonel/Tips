# データ移行時に 2 つの PostgreSQL の定義を突き合わせる方法と、dblink を使うビューの接続先を一括で付け替える方法

サーバー移行のとき、移行元と移行先で DB の定義に差がないことを確認する手順と、dblink の接続先 IP を書いたビューを移行後に作り直す手順のメモ。

（2020-02〜2020-04 時点のメモ。PostgreSQL のバージョンはメモに記録なし。ホスト・DB・ユーザー名は仮の名前に置き換えた）

## 定義の突き合わせ

両方のサーバーで、スキーマだけのダンプを取って `diff` する。

```sh
pg_dumpall -h <ホスト> -U postgres -s > dump_s_<ホスト名>.txt
```

メモの作成者は、あとで `pg_dumpall -s` だけで十分だと判断した。ロール、テーブルスペース、全 DB のスキーマが 1 本に出るため。`pg_dump -s -d <DB名>` は DB 単位で比べたいときに使う。

`pg_dumpall -s` で見えにくい差は、psql のメタコマンドの出力で補う。`\o` で出力先を切り替えて保存し、`diff` や WinMerge で比べる。

```
\o table_list.txt
\dt+
\o
```

比べる対象のメタコマンドは次のとおり。`\l`、`\dt`、`\dm`、`\di+`、`\dn+`、`\df+`、`\ds+`、`\du+`、`\dp`、`\des`、`\det`、`\deu`、`\dy`。

## dblink を使うビューの接続先を付け替える

移行で接続先の IP が変わると、ビュー定義に埋まっている dblink の接続文字列を直す必要がある。ダンプからその定義だけを取り出し、IP を置換して流し直す。

```sh
# 1. スキーマだけをダンプする
pg_dump -U postgres -s <DB名> > view_dblink.dump

# 2. 1 文を 1 行にして、旧 IP を含む文だけを抜き出して置換し、CREATE OR REPLACE VIEW に書き換える
echo '\connect <DB名> <オーナー>' > replace.ddl
cat view_dblink.dump \
  | perl -pe 's/\n/ /g' | perl -pe 's/\r//g' \
  | perl -pe 's/\;/\;\n/g' \
  | grep -E '[^0-9]<旧IP>\s' \
  | perl -pe 's/<旧IP>/<新IP>/g' \
  | perl -pe 's/^ Owner: <オーナー> --  CREATE VIEW/CREATE OR REPLACE VIEW/g' \
  >> replace.ddl

# 3. 実行する
psql -U <ユーザー> -d <DB名> -f replace.ddl

# 4. 件数を突き合わせる（ダンプ内の旧 IP の数と、置換後ファイル内の新 IP の数が一致すること）
grep -o '<旧IP>' view_dblink.dump | wc -l
grep -o '<新IP>' replace.ddl | wc -l
```

要点は 2 つ。`;` で改行して 1 文を 1 行にすることで、`grep` で旧 IP を含む文だけを抜ける。最後に件数を比べて、置換漏れがないことを確かめる。IP の直前を `[^0-9]` で縛るのは、別の IP の末尾に部分一致するのを避けるため。ビューのオーナーが複数あるときは、`Owner:` の行を置換する正規表現をオーナーの数だけ並べる。
