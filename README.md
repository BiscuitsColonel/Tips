# Tips

少しググっただけでは見つけにくい IT の知識をメモする。

書き方のルールは [.claude/rules/writing.md](.claude/rules/writing.md) にある。

## AWS

- Backup / [EBS スナップショットから EC2 を復旧する手順と、AWS Backup から EFS を復元したときの置き場所](AWS/Backup/AWS-Backupからの復元手順（EC2のEBSとEFS）.md)
- CDK / [CDK（TypeScript）の L1 コンストラクトで ALB と Auto Scaling グループを組み、userdata に設定ファイルを埋め込む](AWS/CDK/CDKのL1でALBとASGを組み、userdataへ設定ファイルを埋め込む.md)
- CloudWatch / [AWS の監視で決めたアラートのしきい値・通知レベルと、CloudTrail 由来アラートを受けたときの初動](AWS/CloudWatch/AWSの監視で決めたアラート基準と通知レベル、CloudTrail系アラートの初動.md)
- CloudWatch / [CloudWatch Agent の設定ウィザードで詰まる点（collectd の types.db エラーとパラメータストア名）](AWS/CloudWatch/CloudWatchAgentの設定ウィザードで詰まる点.md)
- CloudWatch / [CloudWatch Logs を Firehose と Lambda で加工して S3 へ出力する（gzip の扱い）](AWS/CloudWatch/CloudWatchLogsをFirehoseとLambdaで変換してS3へ出力する.md)
- EC2 / [Amazon Linux 2 で OpenSSL 1.1.1 を自前ビルドし、httpd の mod_ssl だけを作り直して差し替える](AWS/EC2/AmazonLinux2でhttpdのmod_sslだけOpenSSL1.1.1でビルドし直す.md)
- EC2 / [インターネットアクセスの無い EC2 で yum を使う（S3 の Gateway 型 VPC エンドポイント）](AWS/EC2/インターネットアクセス無しでyumを使う.md)
- ECS / [ECS のサービス間通信：ELB と Cloud Map（サービス検出）の違い](AWS/ECS/ELBとCloudMapの違い.md)
- EventBridge / [EventBridge のイベントパターンを `aws events test-event-pattern` で確認する](AWS/EventBridge/test-event-patternでイベントパターンを確認する.md)
- Glue / [Glue ジョブのネットワーク設計とワーカー数の落とし穴（VPC・サブネット・S3 エンドポイント・IP 枯渇）](AWS/Glue/Glueジョブのネットワークとワーカー数の落とし穴.md)
- SSM / [Session Manager を IP 制限する IAM ポリシーと、Patch Manager でインスタンスを一時的に対象外にする方法](AWS/SSM/SessionManagerのIP制限とPatchManagerの対象外指定.md)
- VPC / [NLB はクロスゾーン負荷分散が無効だと、稼働中のターゲットが無い AZ に振られて通信が失敗する](AWS/VPC/NLBのクロスゾーン負荷分散を有効にしないとAZ間で偏る.md)

## Ansible

- [自作 playbook「HAProxy + Pacemaker で冗長化した Web / SMTP 振り分け環境」の構成と順序依存](Ansible/ansible-haproxy_HAProxyとPacemakerとnginxとpostfixの構築playbook.md)
- [自作 playbook「PostgreSQL + Zabbix 構築」: 何をするものか、冪等にした書き方、bash 履歴の syslog 化](Ansible/ansible-zabbix_PostgreSQLとZabbixを冪等に構築するplaybook.md)
- [Ansible の ignore_errors・failed_when・check_mode・Gathering Facts を実際に動かして確かめた挙動](Ansible/ignore_errorsとfailed_whenとcheck_modeの挙動の違い.md)

## Container

- [VirtualBox + Vagrant で CentOS 6/7 の検証 VM を複数台立てる Vagrantfile の構成](Container/VirtualBoxとVagrantで複数台の検証VMを立てる構成メモ.md)

## DB

- Aurora / [Aurora PostgreSQL のリーダーインスタンスを変更すると、リーダー接続はどうなるか](DB/Aurora/リーダーインスタンス変更中の接続の挙動.md)
- MySQL / [MySQL のトリガー・シーケンステーブル・イベントで予約枠の整合性をデータベース側に持たせる設計例](DB/MySQL/トリガーとシーケンステーブルとイベントで予約枠を管理する設計例.md)
- PostgreSQL / [psql の COPY をファイル分割とテーブル分割で並列実行する投入シェルの設計と落とし穴](DB/PostgreSQL/COPYを並列実行してデータ投入を速くするシェルの設計.md)
- PostgreSQL / [effective_io_concurrency をビットマップヒープスキャンで試した結果（1 → 0 で 20.9 秒が 3.6 秒）](DB/PostgreSQL/effective_io_concurrencyの効果を計測した.md)
- PostgreSQL / [join_collapse_limit は結合全体ではなく、結合ツリーの塊ごとに効く](DB/PostgreSQL/join_collapse_limitは結合ツリーの塊ごとに効く.md)
- PostgreSQL / [json 列に \u0000 が入っていて ->> や -> がエラーになるときの対処と、json/jsonb を NoSQL 的に使うときの注意](DB/PostgreSQL/jsonの列にNULL文字が入っていて取り出せないときの対処.md)
- PostgreSQL / [pg_dump / pg_restore の -c と -C の挙動、DB・テーブル複製の手順](DB/PostgreSQL/pg_dumpとpg_restoreのオプション挙動の検証.md)
- PostgreSQL / [pg_hint_plan の Leading ヒントが効かないときは join_collapse_limit を疑う](DB/PostgreSQL/pg_hint_planで結合順を指定できないときの対処.md)
- PostgreSQL / [pg_rman でフルと増分を回す運用の勘所（保持期間の数え方・PITR の注意）](DB/PostgreSQL/pg_rmanによる日次バックアップ運用の勘所.md)
- PostgreSQL / [pg_statsinfo と pg_dbms_stats で踏んだ点（リポジトリ肥大・不正文字のループ・スキーマ不在）](DB/PostgreSQL/pg_statsinfoとpg_dbms_statsで踏んだ点.md)
- PostgreSQL / [Pgpool-II の運用で分かった、マニュアルだけでは気づきにくい挙動](DB/PostgreSQL/Pgpool-IIの運用で分かった挙動.md)
- PostgreSQL / [PGroonga のインデックスを、レプリケーション構成で別テーブルに作ってから名前を入れ替えて作り直す手順](DB/PostgreSQL/PGroongaのインデックスをレプリケーション構成で作り直す手順.md)
- PostgreSQL / [PGroonga のインデックスを持つテーブルを入れ替えて更新する運用と、壊れたときの掃除、レプリカへの WAL 反映待ち](DB/PostgreSQL/PGroongaのテーブル入れ替え運用とWAL反映待ちのプロシージャ設計.md)
- PostgreSQL / [PostgreSQL 12 のレプリケーションで試した、フェイルオーバー後の切り戻しと、論理レプリケーションが競合で止まったときの読み飛ばし](DB/PostgreSQL/PostgreSQL12のレプリケーションで試した切り戻しと論理レプリケーションの競合対応.md)
- PostgreSQL / [PowerGres（PostgreSQL 派生製品）の運用で踏んだ問題と対処](DB/PostgreSQL/PowerGresの運用で踏んだ問題と対処.md)
- PostgreSQL / [COPY から INSERT 文を作る、ログの実行時間を SQL ごとに集計する、継承パーティションを一括で作るシェルのメモ](DB/PostgreSQL/psqlとシェルで作った小さな運用スクリプトのメモ.md)
- PostgreSQL / [RPM と systemd で PostgreSQL・pgpool-II を運用するときに踏みやすい点（daemon-reload、contrib、pgpool_status）](DB/PostgreSQL/RPMとsystemdで運用するときに踏みやすい点とpgpoolのstatus復旧.md)
- PostgreSQL / [VACUUM のログの読み違えと、ロック・排他まわりの挙動メモ](DB/PostgreSQL/VACUUMとロックで分かった挙動.md)
- PostgreSQL / [WAL の書き込み量を測る方法と、pg_waldump で中身を覗くときの注意](DB/PostgreSQL/WALの書き込み量を測り中身を覗く.md)
- PostgreSQL / [PostgreSQL のサポート問い合わせで分かった、マニュアルを読んだだけでは気づきにくい挙動](DB/PostgreSQL/サポート問い合わせで分かった挙動メモ.md)
- PostgreSQL / [主キーの重複・インデックス破損・truncate の Permission denied を切り分ける](DB/PostgreSQL/データ破損と主キー重複の切り分け.md)
- PostgreSQL / [データ移行時に 2 つの PostgreSQL の定義を突き合わせる方法と、dblink を使うビューの接続先を一括で付け替える方法](DB/PostgreSQL/データ移行時のDB定義の突き合わせとdblink接続先の付け替え.md)
- PostgreSQL / [PostgreSQL のパーティションテーブルを使うべき場面と、実クエリでの速度比較](DB/PostgreSQL/パーティションテーブルの使いどころと速度比較.md)
- PostgreSQL / [PostgreSQL 9.2 から 12 へ上げるときに、既存の SQL・スクリプト・設定が壊れる変更と調べ方](DB/PostgreSQL/メジャーバージョンアップ時に確認する非互換変更と調べ方9.3から12.md)
- PostgreSQL / [メモリ消費・バックアップ・クライアント接続まわりで分かった挙動（サポート問い合わせより）](DB/PostgreSQL/メモリ消費とバックアップと接続で分かった挙動.md)
- PostgreSQL / [PostgreSQL のレプリケーションで WAL が足りなくなる・同期が切れる・切り替えで迷うときの挙動メモ](DB/PostgreSQL/レプリケーションとWAL保持で分かった挙動.md)
- PostgreSQL / [PostgreSQL の性能・運用に効く Linux カーネル設定と postgresql.conf の値の選び方](DB/PostgreSQL/性能と運用に効くOS設定とpostgresql.confの設定値の目安.md)
- PostgreSQL / [自作ベンチマークスクリプトの作り方: 設定値を総当たりで変える pgbench、並列 INSERT、PostgreSQL と MongoDB の比較](DB/PostgreSQL/自作ベンチマークスクリプトの作り方_設定値スイープと並列INSERTとMongoDB比較.md)
- SQLServer / [SQL Server のバックアップを別サーバーにリストアするときに出たエラー二つ（排他アクセスが取れない、ファイルを復元できない）](DB/SQLServer/SQLServerのバックアップを別サーバーにリストアするときに出たエラー二つ.md)

## Design

- [AWS 環境の保守と障害一次対応を外部へ委託するときに先に決めておくこと](Design/AWS環境の保守と一次対応を外部へ委託するときに決めておくこと.md)
- [DDD とクリーンアーキテクチャ まとめ](Design/DDDとクリーンアーキテクチャの整理.md)
- [TODO アプリのシステム設計を AWS で組む（負荷見積もりから通知・リマインドまで）](Design/TODOアプリのシステム設計をAWSで組む.md)

## HA

- [DRBD の下の LVM を拡張したあと create-md が「Device size would be truncated」で拒否されるときの回避](HA/DRBDのディスクを拡張するときcreate-mdが拒否される場合の回避.md)
- [HAProxy を Pacemaker で冗長化し、バックエンドは自動で切り戻さない構成の設計と設定値の理由](HA/HAProxyをPacemaker2台で冗長化しバックエンドを手動切り戻しにする設計.md)
- [LVS（NAT 方式）+ Keepalived で負荷分散と冗長化を組むときの前提と注意点](HA/LVSとKeepalivedの構築で押さえる点.md)
- [NLB 配下の HAProxy 冗長化（Pacemaker）を障害種別ごとに落として確認した結果と、切り替え時間の見積もり](HA/NLB配下のHAProxy冗長化のフェイルオーバー試験とダウンタイム見積もり.md)
- [Pacemaker で PostgreSQL ストリーミングレプリケーションを組むときに外せない点と動作確認の見方](HA/PacemakerでPostgreSQLレプリケーションを組むときの注意点.md)
- [Pacemaker + DRBD + PostgreSQL（CentOS 7）で先にやっておく systemd 修正とリポジトリ除外](HA/PacemakerとDRBDでPostgreSQLを組むときのsystemdユニット修正とリポジトリ除外.md)
- [Pacemaker の切り替え操作で制約が残る問題と、fail-count・cleanup の扱い](HA/Pacemakerのリソース移動で制約が残る問題とfail-countの扱い.md)

## IDE

- Eclipse / [Eclipse の設定](IDE/Eclipse/設定.md)
- IntelliJ / [IntelliJ IDEA で XML を整形すると SQL に差分が出るのを防ぐ](IDE/IntelliJ/設定.md)

## Linux

- [Ansible のインベントリで、ホストが STAGING か PRODUCTION のどちらか一方だけに属しているか事前チェックする](Linux/Ansibleでホストが本番とステージングの両方に属していないか事前チェックする.md)
- [bash を SYSLOG_HISTORY 付きで再コンパイルし、全ユーザーのコマンド履歴を rsyslog に残す](Linux/bashのコマンド履歴をrsyslogに集める再コンパイル手順.md)
- [cron だけで N 世代を使い回すバックアップ（日数を N で割ったあまりをサフィックスにする）](Linux/cronでN世代を使い回すバックアップ.md)
- [EC2（RHEL / Amazon Linux）の初期構築で、ロケール・タイムゾーン・ホスト名を cloud-init の初期化対象から外す](Linux/EC2初期構築でcloud-initに初期設定を上書きさせない.md)
- [logrotate を決まった時刻に回し、ローテート後の日付を前日にそろえ、失敗を syslog に残す](Linux/logrotateを決まった時刻に回し日付と失敗を管理する運用.md)
- [Windows のイベントログを nxlog で Linux の rsyslog に UDP 転送する](Linux/WindowsイベントログをnxlogでrsyslogにUDP転送する.md)
- [Ubuntu・CentOS 7 のデスクトップへ VNC で接続するときの暗号化エラーと再起動時の対処](Linux/デスクトップ環境へVNCで接続するときの落とし穴.md)
- [DB サーバーのバックアップ先に CIFS/NFS 共有をマウントするときの勘所（マウント先の作り方と UID/GID の揃え方）](Linux/バックアップ用の共有ストレージをfstabでマウントするときの勘所.md)
- [EOL した CentOS の yum 復旧・旧バージョン導入と、Ubuntu の dpkg 上書きエラー対処](Linux/古いOSのパッケージ管理トラブル対処.md)

## Middleware

- [Apache 2.2 の httpd.conf を 2.4 に持ち込んだときに出るエラーと対処](Middleware/Apache2.2から2.4へhttpd.confを持ち込んだときのエラーと対処.md)
- [rsyslog の標準スキーマを PostgreSQL のパーティションテーブルにするときに変える点](Middleware/rsyslogのログをPostgreSQLのパーティションテーブルに入れるときの変更点.md)
- [Spark 2.4 の SQL で日本語の列名を書くと ParseException になる（バッククォートで回避）](Middleware/Spark2.4のSQLで日本語の列名がParseExceptionになるときの回避.md)

## Monitoring

- [Pacemaker・DRBD・corosync の異常を、重み付きの整数 1 つにして Zabbix へ送る](Monitoring/Pacemaker・DRBD・corosyncの異常を1つのZabbix項目に重み付き整数で載せる.md)
- [rsyslog の停止を、ログの更新と cron の生存の 2 項目で見張って自動再起動する](Monitoring/rsyslogの停止をログの更新とcronの生存の2項目で見張る.md)
- [Zabbix のアクティブチェックが動かないときのエラーメッセージ別の確認点](Monitoring/Zabbixのアクティブチェックが動かないときの確認点.md)
- [Zabbix のグラフを日本語にする設定と、pg_monz で PostgreSQL / Pgpool-II を監視する前提設定](Monitoring/Zabbixのグラフの日本語化とpg_monzの前提設定.md)

## Security

- [バッチで KMS のデータキーを使い、AES-CTR で項目を暗号化する](Security/KMSのデータキーとAES-CTRでバッチの項目を暗号化する.md)
- [複数サーバーのパスワード定期変更を、管理用 DB 1つから一括で反映する](Security/パスワード定期変更を管理用DBで一括反映する.md)

## SpringBoot

- [Spring Boot のコンテキストパスを設定する](SpringBoot/コンテキストパスの設定.md)

## Terraform

- [Terraform の ignore_changes で RDS の再作成や秘密値の上書きを避ける](Terraform/ignore_changesで再作成と値の上書きを避ける.md)
- [Terragrunt で tfstate をリソース単位に分割して運用するときの勘所](Terraform/Terragruntでtfstateを分割して運用するときのメモ.md)
- [.terraform.lock.hcl の zh と h1 の違いと、複数プラットフォームで checksum が合わないときの考え方](Terraform/プロバイダのロックファイルのzhとh1.md)
- [terraform plan・apply を速くする](Terraform/高速化.md)

## Windows

- [PC を経由して PS4 などの機器をインターネットに繋ぐ（ブリッジ接続と ForceCompatibilityMode）](Windows/PCからPS4へLANを繋ぐブリッジ接続とForceCompatibilityMode.md)
- [PowerShell と VBScript で、スヌーズ付きの Windows トースト通知（リマインダー）を出す](Windows/PowerShellとVBScriptでスヌーズ付きトースト通知を出す.md)
- [Tera Term マクロで SSH に自動ログインする（パスワード認証・鍵認証・踏み台経由）](Windows/TeraTermマクロでSSH自動ログイン.md)

## Work

- PC / [PC のセットアップ（macOS）](Work/PC/setup.md)
