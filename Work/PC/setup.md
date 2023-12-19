# インストール
- [Visual Studio Code](https://code.visualstudio.com/)
  - [MS-CEINTL.vscode-language-pack-ja](https://marketplace.visualstudio.com/items?itemName=MS-CEINTL.vscode-language-pack-ja)
  - [hashicorp.terraform](https://marketplace.visualstudio.com/items?itemName=HashiCorp.terraform)
  - [esbenp.prettier-vscode](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
  - [ms-vscode-remote.remote-ssh](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)
  - [hediet.vscode-drawio](https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio)
  - [OpenAPI (Swagger) Editor](https://marketplace.visualstudio.com/items?itemName=42Crunch.vscode-openapi)
  - [openapi-lint](https://marketplace.visualstudio.com/items?itemName=mermade.openapi-lint)
- [Homebrew](https://brew.sh/index_ja)
  - brew install --cask background-music
  - brew install peco
  - brew install --cask intellij-idea-ce
  - brew install --cask visual-studio-code
  - brew install --cask pgadmin4
  - brew install --cask android-studio
  - brew install --cask slack
  - brew install zsh-autosuggestions
  - brew install zsh-syntax-highlighting
  - brew install --cask docker
  - brew install awscli
  - brew install session-manager-plugin
  - brew install grep gawk gzip gnu-tar gnu-sed gnu-time gnu-getopt jq
  - brew install binutils findutils diffutils coreutils moreutils
  - brew install aws-vault
    - aws-vault add dev_terraform
    - aws-vault add prod_terraform
    - aws-vault exec PROFILE -- commands
  - brew install aws-mfa
    - aws-mfa --profile mfa --device arn:aws:iam::XXXXXXXXXXXX:mfa/USER
  - brew install go
  - brew install openjdk@11 openjdk@17 openjdk@21
  - brew install jenv
    - jenv doctor
    - jenv add /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home
    - jenv add /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
    - jenv add /opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
    - jenv global 21.0
  - brew install tfenv
    - tfenv use 1.6.5
  - brew install nodebrew
    - nodebrew setup_dirs
    - nodebrew setup
    - nodebrew install-binary stable
    - nodebrew use v18.15.0
  - brew install pandoc
    - npm install --global mermaid-filter
    - pandoc README.md --from=markdown --to=docx --standalone --output=cloudhsm.docx --filter=mermaid-filter
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
# jEnv
export JENV_ROOT="$HOME/.jenv"
if [ -d "${JENV_ROOT}" ]; then
  export PATH="$JENV_ROOT/bin:$PATH"
  eval "$(jenv init -)"
fi
# -------------------------------------------------

# -------------------------------------------------
# エイリアス
alias la='ls -la'
alias ll='ls -la'
alias terraform_dev_plan='aws-vault exec dev_terraform -- terraform plan --parallelism=30'
alias terraform_dev_apply='aws-vault exec dev_terraform -- terraform apply --parallelism=30'
alias terraform_dev_init='aws-vault exec dev_terraform -- terraform init -upgrade'
alias terraform_prod_plan='aws-vault exec prod_terraform -- terraform plan --parallelism=30'
alias terraform_prod_apply='aws-vault exec prod_terraform -- terraform apply --parallelism=30'
alias terraform_prod_init='aws-vault exec prod_terraform -- terraform init -upgrade'
alias login_dev='terminal-color "Pro" && aws --profile dev_bastion ssm start-session --target i-XXXXXXX ; terminal-color "Basic"'
alias login_stg='terminal-color "Pro" && aws --profile dev_bastion ssm start-session --target i-YYYYYYY ; terminal-color "Basic"'
alias login_prod='terminal-color "Novel" && aws --profile prod_bastion ssm start-session --target i-ZZZZZZZ ; terminal-color "Basic"'
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
