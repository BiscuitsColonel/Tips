# 設定
## 言語の切り替え
IDEAの画面言語のデフォルトは英語です。英語が苦手な方のために日本語で表示できるようにしましょう。  
日本語化のプラグインはバージョン2020.1.1以降のIDEAで利用することができます。
![image](https://user-images.githubusercontent.com/74767283/229340238-948c674f-592b-4a7f-9205-6c715f63cc8f.png)

## 外観
初心者でも操作しやすいように、ツールバーを表示します。  
設定するとウインドウにツールバーが表示され、一部の操作ができます。「表示」→「外観」→「ツールバー」を選択します。
![image](https://user-images.githubusercontent.com/74767283/229340255-b6d0986b-11e4-4570-a8aa-b99f46f0e5f7.png)

## コード補完の設定
IDEAの補完機能では、デフォルトで大文字と小文字を区別します。  
大文字と小文字を区別する場合は、例えばJavaコードファイルに「stringBuffer」（sは小文字）と入力しても補完機能は表示されませんが、「StringBuffer」と入力すれば補完機能が表示されます。  
大文字と小文字を区別しない場合は、「環境設定」の「エディター」→「一般」→「コード補完」で「大/小文字を区別する」のチェックを外してください。
![image](https://user-images.githubusercontent.com/74767283/229340270-2e0b42ec-1987-4beb-9822-463f06ac8be0.png)

## コードスタイルの設定
インポートするクラス数を設定しないままコーディングをすると、インポートしたクラスがすべて表示され、コードが読みづらくなってしまいます。  
「環境設定」の「エディター」→「コードスタイル」→「Java」で「✳︎でインポートするクラス数」を変更し、指定のクラスの数を超えたら「✳︎」でインポートするように設定します。
![image](https://user-images.githubusercontent.com/74767283/229340286-154b397a-17f8-4852-8f0f-24f90296f7cc.png)

xmlについてはスペースを強制的に1つに揃えようとするため(SQLに差分が出る)、必ず以下の設定を行なってください。
![image](https://user-images.githubusercontent.com/74767283/229340292-20f3ce36-f4a3-44d3-b603-cdeef7514623.png)

## コンパイル
IDEAでは自動コンパイル設定がオフになっています。  
忘れないように、「自動的にプロジェクトをビルドする」にチェックを入れましょう。
![image](https://user-images.githubusercontent.com/74767283/229340307-2cb66989-8e35-40ea-85c6-74840b364bcb.png)

## ショートカットキー
IDEAのショートカットは、Eclipseのショートカットとはまったく異なります。  
新しいショートカットを1から学ぶのは面倒くさいと感じるかもしれませんが、IDEAではそんなEclipseユーザーのために、Eclipseのショートカットを模倣したEclipseキーマップを提供しています。  
これで、IDEAでもEclipseのショートカットを利用できます。
![image](https://user-images.githubusercontent.com/74767283/229340322-57a614ca-dcd8-4172-b7c1-983d0493f92e.png)

## Web開発のプラグイン
### google-java-format
IntelliJ IDEA > Preferences > プラグイン で google-java-format をインストールします。  
IntelliJ IDEA でファイル保存時にコードを整形するように、  
IntelliJ IDEA > Preferences > その他の設定 > google-java-format Settings で Enable google-java-format にチェックを入れ、  
IntelliJ IDEA > Preferences > ツール > 保存時のアクション で コードの整形 にチェックを入れます。

### Checkstyle
IntelliJ IDEA > Preferences > プラグイン で CheckStyle-IDEA をインストールします。  
IntelliJ IDEA > Preferences > ツール > Checkstyle を開き、Google Checks にチェックを入れます。  
google_checks.xmlをダウンロードします。  
IntelliJ IDEA > Preferences > エディター > コードスタイル の上の方にある歯車をクリックします。  
次にスキームのインポート > CheckStyle Configuration をクリックし、google_checks.xml を読み込みます。  

### その他
Springプロジェクトは https://start.spring.io/ から作成して配置する。
