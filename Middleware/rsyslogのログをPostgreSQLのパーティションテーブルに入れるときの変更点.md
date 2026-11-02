# rsyslog の標準スキーマを PostgreSQL のパーティションテーブルにするときに変える点

rsyslog の `ompgsql` で PostgreSQL にログを集めるとき、同梱の `pgsql-createDB.sql` をそのまま使うと日付でパーティション分割できない。パーティション化とあわせて直した点、権限の分け方、日次運用のまとめ。

（2020-02 時点のメモ。PostgreSQL 11、rsyslog 同梱のスキーマ。）

## 標準スキーマから変える点

- 標準の `ID serial not null primary key` のままではパーティションテーブルにできない。パーティションキーを主キーに含める必要があるため、主キーは後から複合で付ける

```sql
CREATE TABLE SystemEvents (
    ID serial not null,
    -- 以下は標準のカラム定義のまま
    DeviceReportedTime timestamp without time zone NULL
    -- ...
) PARTITION BY RANGE (DeviceReportedTime);

ALTER TABLE SystemEvents ADD PRIMARY KEY (id, DeviceReportedTime);

-- どの日付にも当てはまらない行の受け皿
CREATE TABLE SystemEvents_default PARTITION OF SystemEvents DEFAULT;
```

- データベースは、標準の `"Syslog"`（`SQL_ASCII`）ではなく、小文字の `syslog` を `UTF8`（`template0` から）で作った
- 前日分だけを見るビューを作っておくと、日次のレポートや確認が楽になる

```sql
CREATE VIEW SystemEventsYesterday AS
SELECT * FROM SystemEvents
WHERE DeviceReportedTime >= current_date - 1
  AND DeviceReportedTime <  current_date;
```

## 権限を分ける

- 書き込み用ロール: `systemevents` への `INSERT` と、`systemevents_id_seq` への `UPDATE` だけ
- 読み取り用ロール: ビューへの `SELECT` だけ

シーケンスへの権限を忘れると、rsyslog が INSERT で失敗する。

## 日次の運用

- 毎日 1:00 に翌日以降のパーティションを作る
- 毎日 2:00 に日次バックアップを取る

## postgresql.conf

値は PGTune（用途は DW、RAM 16GB、CPU 4、接続 100、SSD）の出力を元にした。`shared_buffers = 4GB`、`effective_cache_size = 12GB`、`maintenance_work_mem = 2GB`、`work_mem = 10485kB`、`min_wal_size = 4GB`、`max_wal_size = 8GB`、`checkpoint_completion_target = 0.9`。ログ保管用の構成なので `archive_mode = off`、`restart_after_crash = off` にした。
