# json 列に \u0000 が入っていて ->> や -> がエラーになるときの対処と、json/jsonb を NoSQL 的に使うときの注意

json/jsonb 列に項目を詰めて NoSQL 的に使ったとき（10 万件で試した）に引っかかった点のメモ。型の概念や ACID/BASE の説明は省く。

（2021-05 時点のメモ。検証した PostgreSQL のバージョンはメモに記録なし）

## \u0000 を含む値は取り出せない

`\u0000`（NULL 文字）を含む文字列が入った json から項目を取り出すと、次のエラーになる。

```
ERROR:  unsupported Unicode escape sequence
DETAIL:  \u0000 cannot be converted to text.
```

text に直してから `\u0000` を消して、json に戻せば取り出せる。

```sql
SELECT (regexp_replace(json::text, '\\u0000', '', 'g'))::json->'client_id' FROM t2;
```

データそのものを直さずに済ませるなら、取り出す側でこの形にする。

## 検索とインデックス

- `->>` は text で返る。数値や boolean で比べるときはキャストする。`->` は jsonb を返すので、配下に配列やマップがあるときに使う
- 式インデックスは、検索条件に書く式と同じ式で作る。数値のキーは型変換まで含めて作る

```sql
SELECT * FROM items WHERE (js->>'price')::numeric > 20000;

CREATE INDEX idx_items_price ON items (((js->>'price')::numeric));
CREATE INDEX idx_items_name  ON items ((js->>'name'));
```

## 更新

複数のキーをまとめて直すときは、`jsonb_set` をキーの数だけ重ねるより、`||` で jsonb を連結するほうが書きやすかった（`jsonb_set` との比較検証はしていない）。

```sql
-- 既存のキーは上書き、無いキーは追加される
UPDATE items SET js = js || jsonb_build_object('name', '新しい名前') WHERE js->>'item_cd' = '0000000001';

-- キーの削除
UPDATE items SET js = js - 'name2' WHERE js->>'item_cd' = '0000000001';
```
