<h2>はじめに</h2>
<p>ウィンドウ関数はデータを処理する間、データの「ウィンドウ」を見ています。<br>
“現在のクエリ行に関連している行の集合を対象として計算を行う能力”を提供します。</p>
<p>簡単に言えば、PostgreSQLには現在11個のウィンドウ関数があります。</p>
<ol>
<li><a href="#1">row_number(): 1からNまでの現在行の数を返す</a></li>
<li><a href="#2">rank(): 現在行の順位を返す（ギャップを含む）</a></li>
<li><a href="#3">dense_rank(): 現在行の順位を返す（ギャップを含まない）</a></li>
<li><a href="#4">percent_rank(): 現在行の相対順位</a></li>
<li><a href="#5">cume_dist(): 現在行の相対順位（bis）</a></li>
<li><a href="#6">ntile(): 行をバケットに分割する</a></li>
<li><a href="#7">lag(): 前の行（または前の行の1つ）を返す</a></li>
<li><a href="#8">lead(): 後の行（または後の行の1つ）を返す</a></li>
<li><a href="#9">first_value(): 最初の行の値を返す</a></li>
<li><a href="#10">last_value(): 最後の行の値を返す</a></li>
<li><a href="#11">nth_value(): N番目の行の値を返す</a></li>
</ol>
<h2>大変そうに見えるが簡単</h2>
<p>ウィンドウ関数を使用するためには、OVER()句で”ウィンドウ関数の構文”を用いる必要があります。サンプルテーブルを作成し、それを使って全てのウィンドウ関数に対する例を挙げてみましょう。<br>
この例では、14名の学生が居るクラスを管理しています。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">-- Creating the table
CREATE TEMP TABLE students (
   id serial,
   name text,
   grade int DEFAULT NULL,
   last_seen_in_class date
);

-- Adding some students
INSERT INTO students (name, grade, last_seen_in_class) VALUES ('Jacob', '9', '2014-08-16'), ('Michael', '6', '2014-08-24'), 
                                                              ('Matthew', '7', '2014-08-24'), ('Emily', '5', '2014-08-17'),
                                                              ('Emma', '8', '2014-08-17'), ('Christopher', '9', '2014-08-24'),
                                                              ('Ashley', '10', '2014-08-16'), ('William', '0', '2014-07-18'),
                                                              ('Grace', '3', '2014-08-21'), ('Tyler', '4', '2014-08-20'),
                                                              ('Alexis', '4', '2014-08-24'), ('Alexander', '10', '2014-08-22'),
                                                              ('Victoria', '4', '2014-08-24'), ('Benjamin', '1', '2014-08-24');</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<p>これで学生リストのテーブルができました。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT * FROM students;
 id |    name     | grade | last_seen_in_class 
----+-------------+-------+--------------------
  1 | Jacob       |     9 | 2014-08-16
  2 | Michael     |     6 | 2014-08-24
  3 | Matthew     |     7 | 2014-08-24
  4 | Emily       |     5 | 2014-08-17
  5 | Emma        |     8 | 2014-08-17
  6 | Christopher |     9 | 2014-08-24
  7 | Ashley      |    10 | 2014-08-16
  8 | William     |     0 | 2014-07-18
  9 | Grace       |     3 | 2014-08-21
 10 | Tyler       |     4 | 2014-08-20
 11 | Alexis      |     4 | 2014-08-24
 12 | Alexander   |    10 | 2014-08-22
 13 | Victoria    |     4 | 2014-08-24
 14 | Benjamin    |     1 | 2014-08-24
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>OVER句</h2>
<p>全てのウィンドウ関数にはOVER句が必要です。<br>
ウィンドウ関数は、クエリによって選択された行の一部（あるいは全ての行）を対象として機能します。OVER句を使って、その対象範囲を指定するのです。<br>
最初は、以下の例のようにOVER句の中でORDER BY句を単純に繰り返すことをお勧めします。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">SELECT a, b, c, any_window_function() OVER (ORDER BY a)
FROM foo
ORDER BY a</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span></span></pre></div>
<p>ご覧のとおり、このクエリは”a”列の順序で並べ替えられます。同じORDER BYがOVER句でも使われています。ウィンドウ関数を使いこなせるようになったら、少し時間をかけて <a href="http://www.postgresql.org/docs/9.3/static/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS">ウィンドウ関数呼び出し</a> に関する公式のドキュメントを読んで、完全なOVER句構文を学んでください。</p>
<p>では、ウィンドウ関数をいくつか試してみましょう。</p>
<h2>1. row_number(): 1からNまでの現在の行の数を返す</h2>
<p>例えば、成績で並び替えて各行の数を知ることができます。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT ROW_NUMBER() OVER (ORDER BY grade), id, name, grade
FROM students
ORDER BY grade;
 row_number | id |    name     | grade 
------------+----+-------------+-------
          1 |  8 | William     |     0
          2 | 14 | Benjamin    |     1
          3 |  9 | Grace       |     3
          4 | 13 | Victoria    |     4
          5 | 11 | Alexis      |     4
          6 | 10 | Tyler       |     4
          7 |  4 | Emily       |     5
          8 |  2 | Michael     |     6
          9 |  3 | Matthew     |     7
         10 |  5 | Emma        |     8
         11 |  6 | Christopher |     9
         12 |  1 | Jacob       |     9
         13 |  7 | Ashley      |    10
         14 | 12 | Alexander   |    10
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>2. rank(): 現在行の順位を返す（ギャップを含む）</h2>
<p>学生リスト内で、成績に応じて各学生の順位を求めることができます（同じ成績の2名は同じ順位になります）。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT rank() OVER (ORDER BY grade DESC), id, name, grade
FROM students
ORDER BY grade DESC;
 rank | id |    name     | grade 
------+----+-------------+-------
    1 | 12 | Alexander   |    10
    1 |  7 | Ashley      |    10
    3 |  6 | Christopher |     9
    3 |  1 | Jacob       |     9
    5 |  5 | Emma        |     8
    6 |  3 | Matthew     |     7
    7 |  2 | Michael     |     6
    8 |  4 | Emily       |     5
    9 | 13 | Victoria    |     4
    9 | 10 | Tyler       |     4
    9 | 11 | Alexis      |     4
   12 |  9 | Grace       |     3
   13 | 14 | Benjamin    |     1
   14 |  8 | William     |     0
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<p>ご覧のとおり、2名が成績10で1位となり、次の2名が成績9で3位に居ます。</p>
<h2>3. dense_rank(): 現在行の順位を返す（ギャップを含まない）</h2>
<p>dense<em>rank()は <a href="#2">rank()</a> と似ていますが、順位間のギャップがありません（rank()では1位の次は3位でしたが、dense</em>rank()では2位になります）。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT dense_rank() OVER (ORDER BY grade DESC), id, name, grade
FROM students
ORDER BY grade DESC;
 dense_rank | id |    name     | grade 
------------+----+-------------+-------
          1 | 12 | Alexander   |    10
          1 |  7 | Ashley      |    10
          2 |  6 | Christopher |     9
          2 |  1 | Jacob       |     9
          3 |  5 | Emma        |     8
          4 |  3 | Matthew     |     7
          5 |  2 | Michael     |     6
          6 |  4 | Emily       |     5
          7 | 13 | Victoria    |     4
          7 | 10 | Tyler       |     4
          7 | 11 | Alexis      |     4
          8 |  9 | Grace       |     3
          9 | 14 | Benjamin    |     1
         10 |  8 | William     |     0
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>4. percent_rank(): 現在行の相対順位</h2>
<p>percent_rank()では、順位の”位置”ではなく、(rank – 1) / (全行数 – 1)という計算をして順位の割合を出します。</p>
<p>下の例では、Christopherは3位に居て14行あるので、percent_rank() = (3 – 2) / (14 – 1) = 2 / 13 = 0.153846153846154です。</p>
<p>学生リストは以下のようになります。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT percent_rank() OVER (ORDER BY grade DESC), id, name, grade 
FROM students
ORDER BY grade DESC;
   percent_rank    | id |    name     | grade 
-------------------+----+-------------+-------
                 0 | 12 | Alexander   |    10
                 0 |  7 | Ashley      |    10
 0.153846153846154 |  6 | Christopher |     9
 0.153846153846154 |  1 | Jacob       |     9
 0.307692307692308 |  5 | Emma        |     8
 0.384615384615385 |  3 | Matthew     |     7
 0.461538461538462 |  2 | Michael     |     6
 0.538461538461538 |  4 | Emily       |     5
 0.615384615384615 | 13 | Victoria    |     4
 0.615384615384615 | 10 | Tyler       |     4
 0.615384615384615 | 11 | Alexis      |     4
 0.846153846153846 |  9 | Grace       |     3
 0.923076923076923 | 14 | Benjamin    |     1
                 1 |  8 | William     |     0
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>5. cume_dist(): 現在行の相対順位（bis）</h2>
<p>cume_dist()では(処理する行数) / (総行数)という計算式で相対順位を計算します。</p>
<p>ChristopherはJacobと並んで3位です。つまりChristopherと同じ順位、またはそれより上位の学生は4人（Christopher、Jacob、Ashley、Alexander）居て、全体では14行あります。</p>
<p>Christopherはcume<em>dist() = 4 / 14 = 0.285714285714286です。<br>
JacobはChristopherと同じ順位なので、cume</em>dist()の結果は同じものを得られるはずです。</p>
<p>学生リストは以下のようになります。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT cume_dist() OVER (ORDER BY grade DESC), id, name, grade 
FROM students
ORDER BY grade DESC;
     cume_dist     | id |    name     | grade 
-------------------+----+-------------+-------
 0.142857142857143 | 12 | Alexander   |    10
 0.142857142857143 |  7 | Ashley      |    10
 0.285714285714286 |  6 | Christopher |     9
 0.285714285714286 |  1 | Jacob       |     9
 0.357142857142857 |  5 | Emma        |     8
 0.428571428571429 |  3 | Matthew     |     7
               0.5 |  2 | Michael     |     6
 0.571428571428571 |  4 | Emily       |     5
 0.785714285714286 | 13 | Victoria    |     4
 0.785714285714286 | 10 | Tyler       |     4
 0.785714285714286 | 11 | Alexis      |     4
 0.857142857142857 |  9 | Grace       |     3
 0.928571428571429 | 14 | Benjamin    |     1
                 1 |  8 | William     |     0
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>6. ntile(): 行をバケットに分割する</h2>
<p>ntile()は行を等しい行数でバケットに分割します。もし10行を2バケットに分ける場合、各バケットには5行ずつとなります。<br>
学生を2つおよび4つのバケットに分割した例を示します。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT id, name, grade,
       ntile(2) OVER (ORDER BY grade DESC) as two_buckets,
       ntile(4) OVER (ORDER BY grade DESC) as four_buckets
FROM students
ORDER BY grade DESC;
 id |    name     | grade | two_buckets | four_buckets 
----+-------------+-------+-------------+--------------
 12 | Alexander   |    10 |           1 |            1
  7 | Ashley      |    10 |           1 |            1
  6 | Christopher |     9 |           1 |            1
  1 | Jacob       |     9 |           1 |            1
  5 | Emma        |     8 |           1 |            2
  3 | Matthew     |     7 |           1 |            2
  2 | Michael     |     6 |           1 |            2
  4 | Emily       |     5 |           2 |            2
 13 | Victoria    |     4 |           2 |            3
 10 | Tyler       |     4 |           2 |            3
 11 | Alexis      |     4 |           2 |            3
  9 | Grace       |     3 |           2 |            4
 14 | Benjamin    |     1 |           2 |            4
  8 | William     |     0 |           2 |            4
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<p>もしntile()を気に入ったのであれば、PostgreSQLの関数である <a href="http://www.gab.lc/articles/weighted_ntile">Weighted_ntile</a> に関する私の記事を読んでみてください。重み付けされたグループでデータに順位を付ける方法を書いています。</p>
<h2>7. lag(): 前の行(または前の行の1つ)を返す</h2>
<p>lag()は現在の行より1つ以上前にある行の値を返します。</p>
<p>以下の例では、現在の行よりも1行または2行前にある学生の名前が表示されています。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT id, name, grade, 
       lag(name, 1) OVER (ORDER BY grade DESC) as one_before, 
       lag(name, 2) OVER (ORDER BY grade DESC) as two_before
FROM students
ORDER BY grade DESC;
 id |    name     | grade | one_before  | two_before  
----+-------------+-------+-------------+-------------
 12 | Alexander   |    10 | {NULL}      | {NULL}
  7 | Ashley      |    10 | Alexander   | {NULL}
  6 | Christopher |     9 | Ashley      | Alexander
  1 | Jacob       |     9 | Christopher | Ashley
  5 | Emma        |     8 | Jacob       | Christopher
  3 | Matthew     |     7 | Emma        | Jacob
  2 | Michael     |     6 | Matthew     | Emma
  4 | Emily       |     5 | Michael     | Matthew
 13 | Victoria    |     4 | Emily       | Michael
 10 | Tyler       |     4 | Victoria    | Emily
 11 | Alexis      |     4 | Tyler       | Victoria
  9 | Grace       |     3 | Alexis      | Tyler
 14 | Benjamin    |     1 | Grace       | Alexis
  8 | William     |     0 | Benjamin    | Grace
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>8. lead(): 後の行（または後の行の1つ）を返す</h2>
<p>lead()は、 <a href="#7">lag()</a> の逆で、現在の行よりも1行以上後にある行の値を返します。</p>
<p>以下の例では現在行の1行または2行後の学生の名前が表示されています。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT id, name, grade, 
       lead(name, 1) OVER (ORDER BY grade DESC) as one_after, 
       lead(name, 2) OVER (ORDER BY grade DESC) as two_after
FROM students
ORDER BY grade DESC;
 id |    name     | grade |  one_after  |  two_after  
----+-------------+-------+-------------+-------------
 12 | Alexander   |    10 | Ashley      | Christopher
  7 | Ashley      |    10 | Christopher | Jacob
  6 | Christopher |     9 | Jacob       | Emma
  1 | Jacob       |     9 | Emma        | Matthew
  5 | Emma        |     8 | Matthew     | Michael
  3 | Matthew     |     7 | Michael     | Emily
  2 | Michael     |     6 | Emily       | Victoria
  4 | Emily       |     5 | Victoria    | Tyler
 13 | Victoria    |     4 | Tyler       | Alexis
 10 | Tyler       |     4 | Alexis      | Grace
 11 | Alexis      |     4 | Grace       | Benjamin
  9 | Grace       |     3 | Benjamin    | William
 14 | Benjamin    |     1 | William     | {NULL}
  8 | William     |     0 | {NULL}      | {NULL}
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>9. first_value(): 最初の行の値を返す</h2>
<p>first_value()はウィンドウフレームの最初の行の値を返します。</p>
<p>例えば、クラスの中の最上位を見て現在の順位と最上位との差を計算できます。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT id, name, grade, 
       first_value(grade) OVER (ORDER BY grade DESC) as best_grade,
       (first_value(grade) OVER (ORDER BY grade DESC) - grade) as difference
FROM students
ORDER BY grade DESC;
 id |    name     | grade | best_grade | difference 
----+-------------+-------+------------+------------
 12 | Alexander   |    10 |         10 |          0
  7 | Ashley      |    10 |         10 |          0
  6 | Christopher |     9 |         10 |          1
  1 | Jacob       |     9 |         10 |          1
  5 | Emma        |     8 |         10 |          2
  3 | Matthew     |     7 |         10 |          3
  2 | Michael     |     6 |         10 |          4
  4 | Emily       |     5 |         10 |          5
 13 | Victoria    |     4 |         10 |          6
 10 | Tyler       |     4 |         10 |          6
 11 | Alexis      |     4 |         10 |          6
  9 | Grace       |     3 |         10 |          7
 14 | Benjamin    |     1 |         10 |          9
  8 | William     |     0 |         10 |         10
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>10. last_value(): 最後の行の値を返す</h2>
<p>last<em>value()はウィンドウフレームの最後の行の値を返します。<br>
公式のドキュメントでは、ウィンドウフレームはデフォルトで”パーティションの先頭から現在の行の最後ピアまで”が含まれるとあります。これではlast</em>valueとnth_valueでは有用ではない結果が得られがちです。以下の例のようにデータ範囲を指定することでこれを回避できます。</p>
<p>クラスの最下位を確認でき、また現在の順位と最下位との差を見ることができます。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT id, name, grade, 
       last_value(grade) OVER (ORDER BY grade DESC RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as worst_grade,
       (last_value(grade) OVER (ORDER BY grade DESC RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) - grade) as difference
FROM students
ORDER BY grade DESC;
 id |    name     | grade | worst_grade | difference 
----+-------------+-------+-------------+------------
 12 | Alexander   |    10 |           0 |        -10
  7 | Ashley      |    10 |           0 |        -10
  6 | Christopher |     9 |           0 |         -9
  1 | Jacob       |     9 |           0 |         -9
  5 | Emma        |     8 |           0 |         -8
  3 | Matthew     |     7 |           0 |         -7
  2 | Michael     |     6 |           0 |         -6
  4 | Emily       |     5 |           0 |         -5
 13 | Victoria    |     4 |           0 |         -4
 10 | Tyler       |     4 |           0 |         -4
 11 | Alexis      |     4 |           0 |         -4
  9 | Grace       |     3 |           0 |         -3
 14 | Benjamin    |     1 |           0 |         -1
  8 | William     |     0 |           0 |          0
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>
<h2>11. nth_value(): N番目の行の値を返す</h2>
<p>nth<em>value()はウィンドウフレーム内のn番目の行を返します。 [last</em>value()](#10) と同様の制約があるため有用な結果を得るためにはデータの範囲を指定する必要があります。</p>
<p>例えば、以下は4位の学生（Jacob）の成績と8位の学生（Emily）の成績が表示されています。</p>
<div class="gatsby-highlight" data-language="prettyprint"><pre style="counter-reset: linenumber NaN" class="language-prettyprint line-numbers"><code class="language-prettyprint">gab@gab # SELECT id, name, grade, 
       nth_value(grade, 4) OVER (ORDER BY grade DESC RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as position_4,
       nth_value(grade, 8) OVER (ORDER BY grade DESC RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as position_8
FROM students
ORDER BY grade DESC;
 id |    name     | grade | position_4 | position_8 
----+-------------+-------+------------+------------
 12 | Alexander   |    10 |          9 |          5
  7 | Ashley      |    10 |          9 |          5
  6 | Christopher |     9 |          9 |          5
  1 | Jacob       |     9 |          9 |          5
  5 | Emma        |     8 |          9 |          5
  3 | Matthew     |     7 |          9 |          5
  2 | Michael     |     6 |          9 |          5
  4 | Emily       |     5 |          9 |          5
 13 | Victoria    |     4 |          9 |          5
 10 | Tyler       |     4 |          9 |          5
 11 | Alexis      |     4 |          9 |          5
  9 | Grace       |     3 |          9 |          5
 14 | Benjamin    |     1 |          9 |          5
  8 | William     |     0 |          9 |          5
(14 rows)</code><span aria-hidden="true" class="line-numbers-rows" style="white-space: normal; width: auto; left: 0;"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span></pre></div>