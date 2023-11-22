# インストール
- [Visual Studio Code](https://code.visualstudio.com/)
  - [MS-CEINTL.vscode-language-pack-ja](https://marketplace.visualstudio.com/items?itemName=MS-CEINTL.vscode-language-pack-ja)
  - [hashicorp.terraform](https://marketplace.visualstudio.com/items?itemName=HashiCorp.terraform)
  - [esbenp.prettier-vscode](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
  - [ms-vscode-remote.remote-ssh](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)
  - [hediet.vscode-drawio](https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio)
- [Homebrew](https://brew.sh/index_ja)
  - brew install --cask background-music
  - brew install peco
  - brew install zsh-autosuggestions
  - brew install zsh-syntax-highlighting
  - brew install --cask docker
  - brew install awscli
  - brew install session-manager-plugin
  - brew install aws-vault
    - aws-vault add dev_terraform
    - aws-vault add prod_terraform
    - aws-vault exec PROFILE -- commands
  - brew install aws-mfa
    - aws-mfa --profile mfa --device arn:aws:iam::XXXXXXXXXXXX:mfa/USER
  - brew install openjdk@11 openjdk@17
  - brew install jenv
    - jenv doctor
    - jenv add $(/usr/libexec/java_home -v "17")
    - jenv add $(/usr/libexec/java_home -v "11")
    - jenv global 17.0
  - brew install tfenv
    - tfenv use 0.14.9
  - brew install nodebrew
    - nodebrew setup_dirs
    - nodebrew setup
    - nodebrew install-binary stable
    - nodebrew use v18.15.0
- [Eclipse](https://mergedoc.osdn.jp/)
- [Android Studio](https://developer.android.com/studio?hl=ja)
- [IntelliJ IDEA](https://www.jetbrains.com/idea/download/)

# .zshrc

```
# -------------------------------------------------
# 環境変数設定
export PATH=$PATH
export LANG=ja_JP.UTF-8
# -------------------------------------------------

# -------------------------------------------------
# オプション設定
setopt share_history
setopt hist_ignore_dups
setopt hist_ignore_all_dups
setopt hist_ignore_space
setopt hist_reduce_blanks
setopt print_eight_bit
# -------------------------------------------------

# -------------------------------------------------
# History設定
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
# -------------------------------------------------

# -------------------------------------------------
# プラグイン有効化
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh
source $(brew --prefix)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
# -------------------------------------------------

# -------------------------------------------------
# pecoの活用
# ctrl + r で過去に実行したコマンドを選択できるようにする。
function peco-select-history() {
  BUFFER=$(\history -n -r 1 | peco --query "$LBUFFER")
  CURSOR=$#BUFFER
  zle clear-screen
}
zle -N peco-select-history
bindkey '^r' peco-select-history
# -------------------------------------------------

# -------------------------------------------------
# 関数
function terminal-color () {
  /usr/bin/osascript -e "tell application \"Terminal\" to set current settings of first window to settings set \"$1\""
}
# -------------------------------------------------

# -------------------------------------------------
# エイリアス
alias la='ls -la'
alias ll='ls -la'
alias terraform_dev_plan='aws-vault exec dev_terraform -- terraform plan --parallelism=30'
alias terraform_dev_apply='aws-vault exec dev_terraform -- terraform apply --parallelism=30'
alias terraform_prod_plan='aws-vault exec prod_terraform -- terraform plan --parallelism=30'
alias terraform_prod_apply='aws-vault exec prod_terraform -- terraform apply --parallelism=30'
alias login_dev='terminal-color "Pro" && aws --profile dev_bastion ssm start-session --target i-022bbe2a107af77f9 ; terminal-color "Basic"'
alias login_stg='terminal-color "Pro" && aws --profile dev_bastion ssm start-session --target i-08261b8394a27576c ; terminal-color "Basic"'
alias login_prod='terminal-color "Novel" && aws --profile prod_bastion ssm start-session --target i-053dca7838ddb9864 ; terminal-color "Basic"'
alias gitman='(){git add . ; git commit -m "$1" ; git push}'
alias gitman='(){git add . ; git commit -m "$1" ; git push}'
# -------------------------------------------------
```
# AWS
## クレデンシャルの登録

```
$ aws configure
```
## ~/.aws/config

```
[default]
region=ap-northeast-1
output=json

[profile dev_bastion]
role_arn=arn:aws:iam::DEVELOP:role/SSM_ROLE
region=ap-northeast-1
mfa_serial=arn:aws:iam::DEVELOP:mfa/IAM_USER
source_profile=default

[profile prod_bastion]
role_arn=arn:aws:iam::PROD:role/SSM_ROLE
region=ap-northeast-1
mfa_serial=arn:aws:iam::DEVELOP:mfa/IAM_USER
source_profile=default

[profile dev_terraform]
role_arn=arn:aws:iam::DEVELOP:role/ADMIN_ROLE
region=ap-northeast-1
mfa_serial=arn:aws:iam::DEVELOP:mfa/IAM_USER

[profile prod_terraform]
role_arn=arn:aws:iam::PROD:role/ADMIN_ROLE
region=ap-northeast-1
mfa_serial=arn:aws:iam::DEVELOP:mfa/IAM_USER

[profile dev_mfa]
role_arn=arn:aws:iam::DEVELOP:role/ADMIN_ROLE
region=ap-northeast-1
source_profile=default

[profile prod_mfa]
role_arn=arn:aws:iam::PROD:role/ADMIN_ROLE
region=ap-northeast-1
source_profile=default

[profile mfa]
region=ap-northeast-1
output=json
```

# SSH
## ~/.ssh/config

```
Host i-* mi-*
    ProxyCommand sh -c "aws --profile dev_bastion ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
```

# Github
## ~/.netrc 

```
machine github.com
login USERNAME
password PASSWORD
```
## config
 - git config --global user.email EMAIL
 - git config --global user.name USERNAME 
