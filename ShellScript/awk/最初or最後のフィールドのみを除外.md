## テスト用ファイル

```sh
$ cat a.txt
1 ls
2 touch test
3 test
4 echo "hoge hoge" > test
```
## コマンド実行
デフォルトの区切り文字は半角スペース

### 最初のフィールドを除外する場合

```sh
$ awk '{$1="";print $0}' a.txt
 ls
 touch test
 test
 echo "hoge hoge" > test
```
### 最後のフィールドを除外する場合

```sh
$ awk '{$NF="";print $0}' a.txt
1 
2 touch 
3 
4 echo "hoge hoge" > 
```
