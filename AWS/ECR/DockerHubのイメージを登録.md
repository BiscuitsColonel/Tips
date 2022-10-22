# 0. ECRリポジトリを作成しておく

```sh
# aws-vault exec dev_terraform -- terraform apply -target=aws_ecr_repository.node_red -target=aws_ecr_repository_policy.node_red
```

# 1. ECRにログイン

```sh
# aws --profile dev_mfa ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 073462688442.dkr.ecr.ap-northeast-1.amazonaws.com
```
# 2. Docker imageを取得

```sh
# docker pull nodered/node-red
```

# 3. Docker imageを確認

```sh
# docker images
REPOSITORY           TAG               IMAGE ID       CREATED         SIZE
nodered/node-red     latest            a15fc0f4e930   5 weeks ago     475MB
```

# 4. image tagを変更

```sh
# docker tag a15fc0f4e930 073462688442.dkr.ecr.ap-northeast-1.amazonaws.com/node_red:latest
```

# 5. imageをpush

```sh
# docker push 073462688442.dkr.ecr.ap-northeast-1.amazonaws.com/node_red:latest
```