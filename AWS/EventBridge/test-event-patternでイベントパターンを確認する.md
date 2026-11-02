# EventBridge のイベントパターンを `aws events test-event-pattern` で確認する

（2021-11 時点のメモ）EventBridge のルールのイベントパターンが、意図したイベントにだけ一致するかを、実際にイベントを発生させずに確認する方法。

## 使い方

パターンとサンプルイベントを渡すと、一致するかを `Result: true/false` で返す。

```sh
$ aws events test-event-pattern \
    --event-pattern '{"source":["aws.guardduty"],"detail":{"severity":[{"numeric":[">=",4]}]}}' \
    --event '{"id":"1","source":"aws.guardduty","detail-type":"GuardDuty Finding","account":"123456789012","region":"ap-northeast-1","time":"2020-12-01T00:00:00Z","detail":{"severity":8.1}}'
{
    "Result": true
}
```

サンプルイベントの `severity` を `2.1` に変えると `false` になる。`--event` には `id`・`source`・`detail-type`・`account`・`region`・`time` などのイベントの必須項目が要る。足りないとエラーになる。

## 便利な場面

GuardDuty の検出結果は、ダッシュボードのサンプル生成機能で作ると約 70 件のイベントが発生し、後続の Lambda や SNS まで動いてしまう。重大度が小数（`8.1`、`2.1` など）なので、数値条件（`numeric`）が想定どおりに効くかを実イベントで試すのは手間がかかる。このコマンドなら、1 件のサンプルで条件の境界を確かめられる。

通知先を作る前に、パターンの正しさだけを先に詰められる。
