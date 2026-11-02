# pg_dump / pg_restore の -c と -C の挙動、DB・テーブル複製の手順

論理バックアップのオプションを実際に流して確かめた結果と、DB の複製・テーブル単位のコピー・サーバー間移行の手順。オプションの一覧は公式ドキュメントを見る。

（2020-10 時点のメモ。PostgreSQL 11.4 で検証。DB 名・テーブル名は仮のもの）

## -c（--clean）と -C（--create）の効き方

- `pg_dump` の `-c` `-C` は、平文形式（`-Fp`）でしか効かない。カスタム形式（`-Fc`）ではダンプ時に指定しても無視され、`pg_restore` 側で指定する。
- `-c` 付きの平文ダンプを `psql` で流すと、先に DROP 文が流れて既存オブジェクトが消える。DROP されるのは、テーブル、ビュー、public 以外のスキーマ。`template0` / `template1` / `postgres` は DROP の対象にならない。
- `-c -C` を一緒に使うと、DB を DROP して作り直す文が入る。接続中の DB は DROP できないので、流す先は別の DB（`postgres` など）に接続して実行する。つまり、ダンプ元と同じ名前の DB を作り直す用途にしか使えない。別名で復元したいなら、先に DB 名を一時的に変えるか、`-C` を使わずに空の DB へ流す。
- `pg_restore` を `-d` なしで実行すると、DB を再構築する SQL が標準出力に出るだけで、DB には何も書かない。`PGDATABASE` 環境変数は使われない。
- `pg_restore -c -d db` は、DB 自体は作り直さず、dump に含まれる名前と同じオブジェクトを削除して追加する。削除対象が無いとエラーが出るが無視してよい。`-a` とは併用できない。
- `pg_restore -C -d postgres` は、接続した DB から `CREATE DATABASE` で dump に含まれる DB を新規作成して、そこへ復元する。`-d` を指定しないときは `-C` は無視される。
- `pg_dump -n スキーマ名` は、指定スキーマと配下のオブジェクトだけを出す。`-h` を付ければリモートからも取れる。

## DB やテーブルを複製する

DB まるごと複製する場合。

```sh
# 使用中でなければ、テンプレート指定が最短（拡張も複製される）
createdb -T コピー元DB 新しいDB

# 使用中でテンプレートにできないとき
createdb 新しいDB
pg_dump -Ft コピー元DB | pg_restore -d 新しいDB
```

別の DB に、同じ名前のテーブルが既にある場合。

```sh
pg_dump -Fc -t a1 -a コピー元DB > table.dump       # データだけ
psql -d コピー先DB -c 'TRUNCATE a1'                # コピー先の a1 を空にする
pg_restore -d コピー先DB table.dump                # データだけを入れる
```

`pg_restore -a` と `-c` は併用できない（上の `pg_restore -c` の項）ので、データだけのダンプに `-c` を付けて消す形にはしない。消すのは `TRUNCATE`（テーブルごと作り直すなら `DROP TABLE` と、定義を含むダンプ）で行う。

別名で追加したいときは、いったん復元してから `ALTER TABLE a1 RENAME TO "A1";` で名前を変える。引用符を付けずに `RENAME TO A1` と書くと、識別子は小文字に畳まれて `a1` のままになる。テーブルが複数ならば `-t` を増やす。数が多ければスキーマ単位か DB 単位で取る。

## サーバー間で移す

```sh
# 定義だけ（-s）。クリーンアップ文付き（-c）で取り、流す前にテーブルスペースの場所を書き換える
pg_dumpall -U postgres -h 移行元IP -s -c > defs.sql
psql -f defs.sql postgres 2> err.txt

# 全体のデータだけ（-a）
pg_dumpall -h 移行元IP -U postgres -a > data.sql
psql -f data.sql postgres 2> err.txt
```

つまずきやすい点。

- ダンプ内のテーブルスペースの場所が移行先に存在しない、または容量が足りないと復元がエラーになる。流す前にダンプを開いて場所を書き換える。
- 拡張が移行先に入っていないと、その拡張に依存するオブジェクトの復元でエラーになる。先にインストールする。
- 復元のエラーは、標準エラーをファイルに出して後で確認する。

## PostgreSQL 11 以降の変更

`GRANT` / `REVOKE` や `ALTER DATABASE SET` といった DB 属性は、以前は `pg_dumpall` でしかダンプされなかった。11 からは `pg_dump --create` / `pg_restore --create` でもダンプ・復元される。

## 関数 1 つだけの定義を取り出す

`pg_dump -t` はテーブル・ビュー・シーケンスしか指定できず、関数は指定できない。カスタム形式のダンプを `pg_restore -P` に渡して取り出す。

```sh
pg_dump -Fc -s DB名 | pg_restore -P 'funcname(integer, text)' > function_define.sql
```

引数の型を正しい個数だけ書く必要がある。分からなければ `pg_dump -Fp -s | less` で探す。`-P` は、公式ドキュメントに「複数の関数は `-P` を複数回指定する」とある（[pg_restore](https://www.postgresql.org/docs/current/app-pgrestore.html)。関数名と引数は、ダンプの目次（`pg_restore -l`）の表記と完全に一致させる）。元のメモには、11.4 で最後の 1 つしか効かなかったとあるが、その版での再現は未確認。確実に取り出したいときは、関数ごとにコマンドを分けて `>>` で追記する。
