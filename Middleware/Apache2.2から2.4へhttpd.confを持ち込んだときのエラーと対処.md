# Apache 2.2 の httpd.conf を 2.4 に持ち込んだときに出るエラーと対処

CentOS 7（httpd 2.4.6）に、2.2 の `httpd.conf` と `conf.d` をそのままコピーして `apachectl configtest` を繰り返したときに出たエラーを、原因別に並べる。コピーしたあとに 1 つずつ直す順番で出会うので、エラー文から引ける形にした。公式の移行ガイドは <https://httpd.apache.org/docs/2.4/upgrading.html>。

（2021-11 時点のメモ。httpd 2.4.6 on CentOS 7。）

## エラー文と対処

| エラー文（抜粋） | 原因 | 対処 |
| --- | --- | --- |
| `Cannot load modules/mod_authn_alias.so into server` | 2.4 に存在しないモジュール | `LoadModule` の行を削除 |
| `Cannot load modules/mod_authn_default.so` / `mod_authz_default.so` | 2.4 で廃止 | 該当の `LoadModule` を削除 |
| `Cannot load modules/mod_disk_cache.so` | 名前が `mod_cache_disk` に変わった | `LoadModule cache_disk_module modules/mod_cache_disk.so` に書き換える |
| `AH00534: httpd: Configuration error: No MPM loaded.` | 2.4 は MPM を `LoadModule` で明示する必要がある | `conf.modules.d` の MPM 設定、または `LoadModule mpm_prefork_module` などを追加 |
| `Invalid command 'Require', perhaps misspelled or defined by a module not included` | `Require` を提供する `authz_core` が未ロード | `LoadModule authz_core_module modules/mod_authz_core.so` を追加 |
| `SSLSessionCache: 'shmcb' session cache not supported` | shmcb が別モジュールになった | `LoadModule socache_shmcb_module modules/mod_socache_shmcb.so` を追加 |
| `Invalid command 'SSLMutex'` | `Mutex` ディレクティブに統合された | `SSLMutex default` を `Mutex default` に置き換える。`AcceptMutex`・`LockFile`・`RewriteLock`・`SSLMutex`・`SSLStaplingMutex`・`WatchdogMutexPath` はすべて `Mutex` に統合された |
| `Cannot load modules/mod_extract_forwarded.so` | 2.4 には無い | `mod_remoteip`（`RemoteIPHeader` など）に置き換える |
| `Invalid command 'User'` / `Group` | `User` と `Group` を提供するのが `mod_unixd` | `LoadModule unixd_module modules/mod_unixd.so` を追加 |
| `Invalid command 'Order'` | 2.2 のアクセス制御の書式。2.4 では `mod_access_compat` に隔離された | `LoadModule access_compat_module modules/mod_access_compat.so` を追加 |
| `Ignoring deprecated use of DefaultType` | 2.4 で廃止予定 | `DefaultType` を削除する |
