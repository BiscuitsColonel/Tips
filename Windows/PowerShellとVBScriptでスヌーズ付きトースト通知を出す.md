# PowerShell と VBScript で、スヌーズ付きの Windows トースト通知（リマインダー）を出す

朝会や作業開始のリマインダーとして、Windows のトースト通知を自作したときの構成。通知の見た目は XML テンプレート、表示は PowerShell、ウィンドウを出さずに起動するのが VBScript のランチャー。

（2020-02 時点のメモ）

## 構成

| ファイル | 役割 |
| --- | --- |
| `sample.xml` | 通知の内容（本文・画像・スヌーズの選択肢）。通知ごとに文言違いで複数作る |
| `toaster.ps1` | XML を読み込んでトースト通知を表示する |
| `powershellLauncher.vbs` | PowerShell のウィンドウを出さずに `toaster.ps1` を起動する |

## 1. XML テンプレート（スヌーズ付き）

`scenario="reminder"` を指定し、スヌーズの時間は `selection` で選ばせる。ボタンは `activationType="system"` で `snooze` と `dismiss` を指定している。

```xml
<toast scenario="reminder">
    <visual>
        <binding template="ToastGeneric">
            <text>朝会の時間です</text>
            <image placement="appLogoOverride" src="C:\path\to\icon.png"/>
        </binding>
    </visual>
    <actions>
        <input id="snoozeTime" type="selection" defaultInput="15">
            <selection id="1" content="1 minute"/>
            <selection id="15" content="15 minutes"/>
            <selection id="60" content="1 hour"/>
            <selection id="240" content="4 hours"/>
            <selection id="1440" content="1 day"/>
        </input>
        <action activationType="system" arguments="snooze" hint-inputId="snoozeTime" content="" />
        <action activationType="system" arguments="dismiss" content=""/>
    </actions>
    <audio silent="true"/>
</toast>
```

`image` の `src` はローカルパスなので、環境ごとに書き換える。

## 2. 表示する PowerShell

テンプレートの XML のパスを引数 `$Args[0]` で受け取る。`$app`（通知の発行元として表示される AppID）は、`Get-StartApps Windows PowerShell` で出る ID を使う。

```powershell
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null

$template = Get-Content $Args[0]
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

# $app ID is the result which 'Get-StartApps Windows PowerShell' command.
$app = '<AppID of Windows PowerShell>'
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show($toast)
```

## 3. ウィンドウを出さずに起動する VBScript

`WScript.Shell.Run` の第2引数を `0` にして PowerShell を呼び、ウィンドウを出さずに起動する。引数は PowerShell スクリプトのパスと XML のパスの2つ。

```vbscript
CreateObject("WScript.Shell").Run "powershell -ExecutionPolicy RemoteSigned -File " + WScript.Arguments(0) + " " + WScript.Arguments(1), 0
```

呼び出しは `wscript.exe powershellLauncher.vbs <toaster.ps1のパス> <XMLのパス>` の形になる。
