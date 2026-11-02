# CloudWatch Logs を Firehose と Lambda で加工して S3 へ出力する（gzip の扱い）

（2021-06 時点のメモ）CloudWatch Logs のログを、不要な行を除いて整形し、S3 に溜める構成。Firehose の変換用 Lambda で gzip を展開して、また圧縮して返す必要がある点が肝。

## 構成

CloudWatch Logs（サブスクリプションフィルター）→ Kinesis Data Firehose（Direct PUT、Lambda で変換）→ S3

- サブスクリプションフィルターに渡されるログは、Firehose の時点でもう gzip 圧縮されている。変換用 Lambda は、`data` を Base64 でデコードしたあと gzip を展開してから中身（`logEvents`）を読む
- 変換結果は、Lambda で gzip 圧縮して Base64 で返す
- Firehose の S3 配信設定で gzip 圧縮を選んでも、拡張子が `.gz` になるだけで中身は圧縮されなかった。CloudWatch Logs 側の gzip との二重圧縮を避ける挙動と思われるが、理由は未確認。圧縮は Lambda の中で行う
- 変換の Lambda のタイムアウトは 1 分にしてある（既定の 3 秒では、レコードが多いと足りなくなる）

## 変換用 Lambda

```python
import base64
import gzip
import io
import json


def lambda_handler(event, context):
    transformed_records = []

    # 複数のレコードが event に渡されるのでループで回す
    for rec in event['records']:
        record_id = rec['recordId']

        # Base64 でデコードし、gzip を展開する
        data = base64.b64decode(rec['data'])
        with gzip.GzipFile(fileobj=io.BytesIO(data), mode='r') as f:
            data = json.loads(f.read())

        processed = ''
        for log_event in data['logEvents']:
            processed += transform(log_event) + '\n'

        # 変換したデータを gzip で圧縮する
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='w') as f:
            f.write(processed.encode('utf-8'))

        transformed_records.append({
            'data': base64.b64encode(buf.getvalue()).decode('utf-8'),
            'result': 'Ok',
            'recordId': record_id,
        })

    return {'records': transformed_records}


def transform(log_event):
    # ここで 1 行ごとの変換を行う（例: JSON の message を取り出す）
    return json.dumps(json.loads(log_event['message']))
```

## サブスクリプションフィルターで行を除く

JSON 形式のログなら、フィルターパターンで特定のロガーを除ける。除きたいものがあるなら、Lambda で捨てるより、フィルターで送らない方が Firehose の料金と Lambda の実行が減る。

```
{ $.logger_name != "NOISY.LOG" }
```

## IAM

- CloudWatch Logs が Firehose に書くためのロールを作る。信頼ポリシーのプリンシパルは `logs.ap-northeast-1.amazonaws.com`（リージョンごとのサービスプリンシパル）、アクションは `sts:AssumeRole`
- そのロールに `firehose:*`（実際は `PutRecord` と `PutRecordBatch` に絞れる）を、対象の配信ストリームの ARN に対して許可する
- Firehose 側のロールには、S3 への書き込みと Lambda の呼び出しの権限が要る

## 配信されたファイルの確認

Firehose が S3 に出したファイルは、ダウンロードして `jq` で見られる。

```sh
$ gunzip -c delivered-file.gz | jq 'select(.logger_name == "Batch")' | jq -r .message | more
```
