# pg_hint_plan の Leading ヒントが効かないときは join_collapse_limit を疑う

pg_hint_plan で結合順を `Leading` で指定したのに、とんでもない実行計画になる／ヒントが通らないときの原因と対処。基本的な導入方法とヒント句の一覧は [pg_hint_plan の公式ドキュメント](https://pghintplan.osdn.jp/pg_hint_plan-ja.html) を見る。

（2021-01 時点のメモ。PostgreSQL 12 + pg_hint_plan 1.3.5 で検証）

## 症状と原因

`join_collapse_limit`（デフォルト 8）は、結合を何テーブルまでプランナが自由に並べ替えるかの上限。検証では 2 にしてあった。結合するテーブルの数（`EXISTS` も結合に展開される）がこの上限を超えていると、`Leading` で指定した順序をプランナが取れず、pg_hint_plan の指定を通そうとして巨大なコスト（`cost=10000000077.30` のような値）を付けた Nested Loop を選ぶ。結果として、ヒントを付けない場合より悪い計画になる。

`from_collapse_limit` も同様に、FROM 句の要素数の上限として効く。

## 対処

ヒントの中で `Set` ヒントを併用し、そのクエリの間だけ上限を引き上げる。

```sql
/*+ Leading((((t1 t3) t4) t2)) Set(join_collapse_limit 8) */
EXPLAIN ANALYZE SELECT t1.txt FROM t1
 WHERE EXISTS (SELECT 1 FROM t2 WHERE t1.id = t2.id)
   AND EXISTS (SELECT 1 FROM t3 WHERE t1.id = t3.id)
   AND EXISTS (SELECT 1 FROM t4 WHERE t1.id = t4.id);
```

`Set(...)` はそのクエリの計画作成中だけ GUC を変える。ヒントなしで同じ検証をして `join_collapse_limit` の値（`SHOW join_collapse_limit;`）が小さくないかを先に確認する。

## hints テーブルで固定するときの落とし穴

`pg_hint_plan.enable_hint_table = on`（`SET` でセッション単位に変えられる。ソースの定義が `PGC_USERSET` で、一般ユーザーも変えられる。<https://github.com/ossc-db/pg_hint_plan/blob/master/pg_hint_plan.c>。全セッションに効かせるなら `postgresql.conf`）にして、`hint_plan.hints` に登録する方式では、クエリ文字列の一致が厳密。

- 登録する `norm_query_string` は、定数を `?` にした形で、末尾の `;` まで含めないと一致しない
- 空白の数も揃える必要がある。末尾にスペースを足しただけでヒントが外れる
- `PREPARE` 文は、`$1` `$2` のままの文を登録する

## 効かない場面

- 埋め込み SQL（ECPG）では、C のプリプロセッサがコメントを消すので、クエリに直接ヒントコメントを書けない。この場合は hints テーブルを使う。`EXECUTE` で動的に実行する SQL に含まれるコメントは有効。
- `pg_stat_statements` はクエリ ID の生成時にコメントを無視するので、ヒントが違うだけの同一クエリは 1 つに集計される。
- ヒントの効きを確かめるには、`pg_hint_plan.debug_print` と `pg_hint_plan.message_level` を上げて、ヒントがどう解釈されたかをログに出す。
