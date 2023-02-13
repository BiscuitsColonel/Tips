# インストール
- [Visual Studio Code](https://code.visualstudio.com/)
  - [MS-CEINTL.vscode-language-pack-ja](https://marketplace.visualstudio.com/items?itemName=MS-CEINTL.vscode-language-pack-ja)
  - [hashicorp.terraform](https://marketplace.visualstudio.com/items?itemName=HashiCorp.terraform)
  - [esbenp.prettier-vscode](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
  - [ms-vscode-remote.remote-ssh](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)
  - [hediet.vscode-drawio](https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio)
- [Homebrew](https://brew.sh/index_ja)
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
    - jenv add `/usr/libexec/java_home -v "17"`
    - jenv add `/usr/libexec/java_home -v "11"`
    - jenv global 17.0
  - brew install tfenv
    - tfenv use 0.14.9
- [Eclipse](https://mergedoc.osdn.jp/pleiades-redirect/2022/pleiades_ultimate-mac_jre.zip.html?v=20221018)
  - [フォーマッター](../../IDE/Eclipse/formatter.xml)
- [Android Studio](https://developer.android.com/studio?hl=ja)

# 環境変数

```
# -------------------------------------------------
# 環境変数設定
export PATH=$PATH
export LANG=ja_JP.UTF-8
# -------------------------------------------------

# -------------------------------------------------
# Alias設定
alias v='vim'
# -------------------------------------------------

# -------------------------------------------------
# オプション設定

# History設定
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
setopt share_history
setopt hist_ignore_dups
setopt hist_ignore_all_dups
setopt hist_ignore_space
setopt hist_reduce_blanks

setopt print_eight_bit
# -------------------------------------------------

# -------------------------------------------------
# プラグイン有効化
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh
source $(brew --prefix)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
# -------------------------------------------------

# -------------------------------------------------
# pecoの活用1
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
# pecoの活用2
# cdr自体の設定
if [[ -n $(echo ${^fpath}/chpwd_recent_dirs(N)) && -n $(echo ${^fpath}/cdr(N)) ]]; then
    autoload -Uz chpwd_recent_dirs cdr add-zsh-hook
    add-zsh-hook chpwd chpwd_recent_dirs
    zstyle ':completion:*' recent-dirs-insert both
    zstyle ':chpwd:*' recent-dirs-default true
    zstyle ':chpwd:*' recent-dirs-max 1000
fi

# ctrl + f で過去に移動したことのあるディレクトリを選択できるようにする。
function peco-cdr () {
    local selected_dir="$(cdr -l | sed 's/^[0-9]\+ \+//' | peco --prompt="cdr >" --query "$LBUFFER")"
    if [ -n "$selected_dir" ]; then
        BUFFER="cd ${selected_dir}"
        zle accept-line
    fi
}
zle -N peco-cdr
bindkey '^f' peco-cdr
# -------------------------------------------------

# -------------------------------------------------
# pecoの活用3
# deで目的のdockerコンテナに接続
alias deb='docker exec -it $(docker ps | peco | cut -d " " -f 1) /bin/bash'
alias dea='docker exec -it $(docker ps | peco | cut -d " " -f 1) /bin/ash'
# -------------------------------------------------

# -------------------------------------------------
# エイリアス
alias la='ls -la'
alias ll='ls -la'
alias terraform_dev_plan='aws-vault exec dev_terraform -- terraform plan --parallelism=30'
alias terraform_dev_apply='aws-vault exec dev_terraform -- terraform apply --parallelism=30'
alias terraform_prod_plan='aws-vault exec prod_terraform -- terraform plan --parallelism=30'
alias terraform_prod_apply='aws-vault exec prod_terraform -- terraform apply --parallelism=30'
alias login_dev='aws --profile dev_bastion ssm start-session --target i-xxxxxxxxxx'
alias login_stg='aws --profile dev_bastion ssm start-session --target i-xxxxxxxxxx'
alias login_prod='aws --profile prod_bastion ssm start-session --target i-xxxxxxxxxx'
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

## ~/.aws/cli/alias 

```
[toplevel]

whoami = sts get-caller-identity

create-assume-role =
  !f() {
    aws iam create-role --role-name "${1}" \
      --assume-role-policy-document \
        "{\"Statement\":[{\
            \"Action\":\"sts:AssumeRole\",\
            \"Effect\":\"Allow\",\
            \"Principal\":{\"Service\":\""${2}".amazonaws.com\"},\
            \"Sid\":\"\"\
          }],\
          \"Version\":\"2012-10-17\"\
        }";
  }; f

running-instances = ec2 describe-instances \
    --filter Name=instance-state-name,Values=running \
    --output table \
    --query 'Reservations[].Instances[].{ID: InstanceId,Hostname: PublicDnsName,Name: Tags[?Key==`Name`].Value | [0],Type: InstanceType, Platform: Platform || `Linux`}'

ebs-volumes= ec2 describe-volumes \
    --query 'Volumes[].{VolumeId: VolumeId,State: State,Size: Size,Name: Tags[0].Value,AZ: AvailabilityZone}' \
    --output table

amazon-linux-amis = ec2 describe-images \
    --filter \
      Name=owner-alias,Values=amazon \
      Name=name,Values="amzn-ami-hvm-*" \
      Name=architecture,Values=x86_64 \
      Name=virtualization-type,Values=hvm \
      Name=root-device-type,Values=ebs \
      Name=block-device-mapping.volume-type,Values=gp2 \
    --query "reverse(sort_by(Images, &CreationDate))[*].[ImageId,Name,Description]" \
    --output text

list-sgs = ec2 describe-security-groups --query "SecurityGroups[].[GroupId, GroupName]" --output text

sg-rules = !f() { aws ec2 describe-security-groups \
    --query "SecurityGroups[].IpPermissions[].[FromPort,ToPort,IpProtocol,join(',',IpRanges[].CidrIp)]" \
    --group-id "$1" --output text; }; f

tostring =
  !f() {
    jp -f "${1}" 'to_string(@)'
  }; f

tostring-with-jq =
  !f() {
    cat "${1}" | jq 'tostring'
  }; f

authorize-my-ip =
  !f() {
    ip=$(aws myip)
    aws ec2 authorize-security-group-ingress --group-id ${1} --cidr $ip/32 --protocol tcp --port 22
  }; f

get-group-id =
  !f() {
    aws ec2 describe-security-groups --filters Name=group-name,Values=${1} --query SecurityGroups[0].GroupId --output text
  }; f

authorize-my-ip-by-name =
  !f() {
    group_id=$(aws get-group-id "${1}")
    aws authorize-my-ip "$group_id"
  }; f

# list all security group port ranges open to 0.0.0.0/0
public-ports = ec2 describe-security-groups \
  --filters Name=ip-permission.cidr,Values=0.0.0.0/0 \
  --query 'SecurityGroups[].{
    GroupName:GroupName,
    GroupId:GroupId,
    PortRanges:
      IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`)].[
        join(`:`, [IpProtocol, join(`-`, [to_string(FromPort), to_string(ToPort)])])
      ][]
  }'

# List or set your region
region = !f() { [[ $# -eq 1 ]] && aws configure set region "$1" || aws configure get region; }; f

find-access-key = !f() {
    clear_to_eol=$(tput el)
    for i in $(aws iam list-users --query "Users[].UserName" --output text); do
      printf "\r%sSearching...$i" "${clear_to_eol}"
      result=$(aws iam list-access-keys --output text --user-name "${i}" --query "AccessKeyMetadata[?AccessKeyId=='${1}'].UserName";)
      if [ -n "${result}" ]; then
         printf "\r%s%s is owned by %s.\n" "${lear_to_eol}" "$1" "${result}"
         break
      fi
    done
    if [ -z "${result}" ]; then
      printf "\r%sKey not found." "${clear_to_eol}"
    fi
  }; f

docker-ecr-login =
  !f() {
    region=$(aws configure get region)
    endpoint=$(aws ecr get-authorization-token --region $region --output text --query authorizationData[].proxyEndpoint)
    passwd=$(aws ecr get-authorization-token --region $region --output text --query authorizationData[].authorizationToken | base64 --decode | cut -d: -f2)
    docker login -u AWS -p $passwd $endpoint
  }; f

myip =
  !f() {
    dig +short myip.opendns.com @resolver1.opendns.com
  }; f

allow-my-ip =
  !f() {
    my_ip=$(aws myip)
    aws ec2 authorize-security-group-ingress --group-name ${1} --protocol ${2} --port ${3} --cidr $my_ip/32
  }; f

revoke-my-ip =
  !f() {
    my_ip=$(aws myip)
    aws ec2 revoke-security-group-ingress --group-name ${1} --protocol ${2} --port ${3} --cidr $my_ip/32
  }; f

allow-my-ip-all =
  !f() {
    aws allow-my-ip ${1} all all
  }; f

revoke-my-ip-all =
  !f() {
    aws revoke-my-ip ${1} all all
  }; f
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
