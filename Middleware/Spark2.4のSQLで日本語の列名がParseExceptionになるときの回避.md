# Spark 2.4 の SQL で日本語の列名を書くと ParseException になる（バッククォートで回避）

Spark SQL に日本語の列名をそのまま書くとパースエラーになる。あわせて、1 万列の CSV を取り込んで JOIN したときの挙動を確認した結果。

（2021-08 時点のメモ。Spark 2.4.8（`spark-2.4.8-bin-hadoop2.7`）、Java 1.8.0_302、Python 3.6.8。）

## 日本語の列名

```text
spark.sql("SELECT 顧客番号 FROM client_table")
-> ParseException: no viable alternative at input 'SELECT 顧'(line 1, pos 7)
```

バッククォートで囲めば通る。

```python
spark.sql("SELECT `顧客番号` FROM client_table").show()
```

## 1 万列のテーブルを取り込んで JOIN

1 万列 x 10 行の CSV を `read.csv(header=True, inferSchema=True)` で取り込み、別テーブルと LEFT JOIN する SQL を実行した。結合は期待どおりに動き、件数も合った。

実行中に次の警告が出るが、動作に問題はなかった。

```text
WARN Utils: Truncated the string representation of a plan since it was too large.
This behavior can be adjusted by setting 'spark.debug.maxToStringFields'.
```
