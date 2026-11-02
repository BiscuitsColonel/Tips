# PC を経由して PS4 などの機器をインターネットに繋ぐ（ブリッジ接続と ForceCompatibilityMode）

有線 LAN が 2 本あり、USB-LAN 変換機を 1 つ使える PC で、PC を経由して PS4 など LAN 機器を繋ぐための設定。ブリッジ接続にして共有機能を使うだけでは、機器側で IP アドレスが取れないことがある。

（2020-08 時点のメモ）

## 構成

- 有線 LAN 2 本（PC 本体のイーサネットと、USB-LAN 変換機のイーサネット 3）
- 本体側がインターネットに繋がっていて、変換機側に PS4 を繋ぐ

## 手順

1. 「ネットワーク接続」画面で、イーサネットとイーサネット 3 を両方選択して右クリックし、「ブリッジ接続」を選ぶ。「ネットワークブリッジ」というアダプターができれば完了
2. ブリッジを作っても機器がインターネットに繋がらないときは、管理者権限のコマンドプロンプトで `ipconfig` を実行し、ブリッジアダプターに DHCP から付与された IP アドレスを確認する。`169.254.…`（APIPA）になっていたら DHCP サーバーに繋がっていない。`ForceCompatibilityMode` を enabled にすると繋がる

```text
C:\WINDOWS\system32>netsh bridge show adapter

 ID AdapterFriendlyName         ForceCompatibilityMode
------------------------------------------------------
  1 イーサネット                      disabled
  2 イーサネット 3                    disabled

C:\WINDOWS\system32>netsh bridge set adapter 1 enable

C:\WINDOWS\system32>netsh bridge show adapter

 ID AdapterFriendlyName         ForceCompatibilityMode
------------------------------------------------------
  1 イーサネット                      enabled
  2 イーサネット 3                    disabled
```

今回はインターネット側（ID 1 のイーサネット）に対して有効にして、ブリッジ接続できた。

## 補足: ネットワークの共有機能は別の方法

「ブリッジ」ではなくネットワークの共有機能で繋ぐ場合は、共有したいネットワークカードを選択して右クリックし、プロパティの「共有」タブを開く。すべてにチェックを入れ、ホームネットワーク接続の項目に共有先のネットワークカードを選ぶ。
