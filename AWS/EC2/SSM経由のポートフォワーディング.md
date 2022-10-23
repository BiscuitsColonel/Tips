<h2 id="toc-1">Session Managerについて</h2>
<p>Session ManagerはAWS Systems Manager(SSM)の機能の一つです。</p>
<p>Session ManagerはEC2インスタンスなどのエージェントがインストールされたマシンとクライアントの間にセッションを作成してくれます。</p>
<p>特徴としてはホスト側がプル式でセッションを作成するため、セキュリティグループによるポートの開放が不要になります。</p>
<p>不必要にポートを解放する必要がなくなり、セキュリティが向上します。</p>
<p>また、Session Mnagerを利用して通信を行うとアクティビティのログが保存可能で、コンプライアンスの観点からも便利です。</p>
<p>今回は、Session Managerの機能をつかってEC2インスタンスのポートをローカルにポートフォワードしてみたいと思います。</p>
<p>こうすることで、セキュリティグループでポートを解放せずともEC2インスタンスのポートにアクセス可能となります。</p>
<h2 id="toc-2">準備</h2>
<p>EC2インスタンスを用意します。
Session Managerを利用するためには以下の3つの条件が揃っている必要があります。</p>
<ul>
<li>SSMのエンドポイントへのアクセスが可能</li>
<li>SSM Agentがインストールされている</li>
<li>適切なIAMロールがインスタンスプロファイルに割り当てられている</li>
</ul>
<p>今回は以下のようなインスタンスを作成しました。</p>
<ul>
<li>Public IPが割り当てられインターネットへのアクセスが可能(SSMのエンドポイントへのアクセスが可能)</li>
<li>マシンイメージはAmazon Linux 2 (SSM Agentはデフォルトでインストール済み)</li>
<li><code>AmazonSSMManagedInstanceCore</code>をインスタンスプロファイルに割り当て済み（インスタンスがSSMにアクセスするのに必要な権限が含まれている）</li>
<li>セキュリティグループのインバウンドは全て拒否、アウトバウンドは全て許可</li>
</ul>
<h2 id="toc-3">接続してみる</h2>
<p>EC2インスタンスに対してポートフォワードを行ってみます。</p>
<p class="file-name"><code>セッションの作成</code></p><pre class="code language-bash" tabindex="0"><code class="language-bash">$ aws ssm start-session --target i-0123456789ABCDEFG <span class="token punctuation">\</span>
                       --document-name AWS-StartPortForwardingSession <span class="token punctuation">\</span>
                       --parameters <span class="token string">'{"portNumber":["22"],"localPortNumber":["10022"]}'</span>
Starting session with SessionId: XXXXXXX
Port <span class="token number">10022</span> opened <span class="token keyword">for</span> sessionId XXXXXXX.
Waiting <span class="token keyword">for</span> connections<span class="token punctuation">..</span>.

<span class="token comment"># SSHなどで通信が開始すると以下のメッセージが表示される。</span>
Connection accepted <span class="token keyword">for</span> session <span class="token punctuation">[</span>XXXXXXX<span class="token punctuation">]</span></code></pre>
<p>今回は、EC2インスタンスの22番ポートをローカルの10022番にポートフォワードしています。</p>
<p>つまりは、ローカルの10022番を利用して通信を行う場合はすべてEC2インスタンスの22番に転送されます。</p>
<p>試しに、SSHで接続してみます。</p>
<p class="file-name"><code>SSHで接続する</code></p><pre class="code language-bash" tabindex="0"><code class="language-bash">$ <span class="token function">ssh</span> ec2-user@localhost -p <span class="token number">10022</span> -i XXXXXXX.pem 
Last login: Tue Mar <span class="token number">29</span> 06:52:33 <span class="token number">2022</span> from localhost

       __<span class="token operator">|</span>  __<span class="token operator">|</span>_  <span class="token punctuation">)</span>
       _<span class="token operator">|</span>  <span class="token punctuation">(</span>     /   Amazon Linux <span class="token number">2</span> AMI
      ___<span class="token operator">|</span><span class="token punctuation">\</span>___<span class="token operator">|</span>___<span class="token operator">|</span>

https://aws.amazon.com/amazon-linux-2/</code></pre>
<p>ローカルホストの10022番に対してアクセスしましたが、EC2インスタンスにつながりました。
無事ポートフォワードが機能していることが確認できました。</p>
<p>このとき注意点として、SSHで接続する場合はEC2に公開鍵が設定されている必要があります。</p>
<p>セッションを作成するまではSSMが行ってくれるので認証情報は必要ありませんが、セッション作成後は単純にSSHでの接続となるので認証情報が必要となります。</p>
<p>今回はsshコマンドの<code>-i</code>オプションで認証情報のファイルを指定しています。</p>
<h3 id="toc-4">SSH Configファイルに設定するともっと便利に</h3>
<p>SSHで接続するたびに毎回AWS CLIでコマンドを叩くのは冗長かもしれません。</p>
<p>SSHのConfigファイルに以下の内容を記述すればもう少し簡単にアクセスできます。</p>
<p class="file-name"><code>~/.ssh/config</code></p><pre class="code language-bash" tabindex="0"><code class="language-bash"><span class="token function">host</span> i-* mi-*
    ProxyCommand <span class="token function">sh</span> -c <span class="token string">"aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"</span></code></pre>
<p>この設定があれば以下のように接続することができます。</p>
<p class="file-name"><code>SSHで接続</code></p><pre class="code language-bash" tabindex="0"><code class="language-bash">$ <span class="token function">ssh</span> ec2-user@i-0123456789ABCDEFG -i ./XXXXXXX.pem 
Last login: Tue Mar <span class="token number">29</span> <span class="token number">17</span>:15:48 <span class="token number">2022</span> from localhost

       __<span class="token operator">|</span>  __<span class="token operator">|</span>_  <span class="token punctuation">)</span>
       _<span class="token operator">|</span>  <span class="token punctuation">(</span>     /   Amazon Linux <span class="token number">2</span> AMI
      ___<span class="token operator">|</span><span class="token punctuation">\</span>___<span class="token operator">|</span>___<span class="token operator">|</span>

https://aws.amazon.com/amazon-linux-2/</code></pre>
<h2 id="toc-5">おまけ</h2>
<p>ポートフォワードで通信を行なっているため、ある程度自由にポートを転送することができます。</p>
<p>いろいろなアプリケーションで接続してみます。</p>
<h3 id="toc-6">SFTP</h3>
<p>先ほどと同様にEC2インスタンスの22番ポートをローカルの10022番にポートフォワードすればSFTPも利用可能です。</p>
<p class="file-name"><code>SFTPで接続</code></p><pre class="code language-bash" tabindex="0"><code class="language-bash">$ <span class="token function">sftp</span> -oPort<span class="token operator">=</span><span class="token number">10022</span> -i XXXXXXX.pem ec2-user@localhost
Connected to localhost.
sftp<span class="token operator">&gt;</span> put ./dummy.txt 
Uploading ./dummy.txt to /home/ec2-user/dummy.txt
./dummy.txt         <span class="token number">100</span>%   <span class="token number">14</span>     <span class="token number">0</span>.5KB/s   00:00    
sftp<span class="token operator">&gt;</span> quit</code></pre>
<h3 id="toc-7">HTTP</h3>
<p>次は別のポートで試してみます。
EC2インスタンスにNginxをインストールし80番ポートをローカルの10080番にポートフォワードします。</p>
<p class="file-name"><code>HTTP</code></p><pre class="code language-bash" tabindex="0"><code class="language-bash">$ aws ssm start-session --target i-0123456789ABCDEFG <span class="token punctuation">\</span>
                       --document-name AWS-StartPortForwardingSession <span class="token punctuation">\</span>
                       --parameters <span class="token string">'{"portNumber":["80"],"localPortNumber":["10080"]}'</span></code></pre>
<p>先ほどと違うのはポート番号だけです。</p>
<p>cURLを用いて、ローカルの10080番にアクセスしてみます。</p>
<p class="file-name"><code>cURLでアクセスする</code></p><pre class="code language-bash" tabindex="0"><code class="language-bash">$ <span class="token function">curl</span> -I http://localhost:10080
HTTP/1.1 <span class="token number">200</span> OK
Server: nginx/1.20.0
Date: Tue, <span class="token number">29</span> Mar <span class="token number">2022</span> 07:19:52 GMT
Content-Type: text/html
Content-Length: <span class="token number">3520</span>
Last-Modified: Thu, <span class="token number">15</span> Jul <span class="token number">2021</span> <span class="token number">21</span>:46:50 GMT
Connection: keep-alive
ETag: <span class="token string">"60f0acca-dc0"</span>
Accept-Ranges: bytes</code></pre>
<p>無事にNginxからリクエストが返ってきました。</p>
<h2 id="toc-8">参考</h2>
<ul>
<li><a href="https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/session-manager.html">AWS Systems Manager Session Manager</a></li>
<li><a href="https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html">セッションを開始する</a></li>
<li><a href="https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/session-manager-getting-started-enable-ssh-connections.html">ステップ 8: (オプション) Session Manager を通して SSH 接続のアクセス許可を有効にして制御する</a></li>
</ul>
