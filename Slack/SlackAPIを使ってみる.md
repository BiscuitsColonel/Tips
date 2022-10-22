1. Slackへ行ってアプリ作成
![](img/app1.png)

2. OAuth & Permissions＞Scopesにてパーミッション追加（channels:read、chat:write:user、files:write:userの３つ）
![](img/app2.png)

3. アプリをワークスペースにインストール
![](img/app3.png)
![](img/app4.png)
![](img/app5.png)

4. 発行されたトークンを利用してchannels.list＞Testerでchannelのidを調べる
![](img/app6.png)

5. プログラム（メッセージ投稿）

```py
import requests

url = "https://slack.com/api/chat.postMessage"
data = {
   "token": "<your oauth access token>",
   "channel": "<your channel id>",
   "text": "Hello world"
}
requests.post(url, data=data)
```
