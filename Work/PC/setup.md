# 環境変数

```
export HISTFILESIZE=10000

alias la='ls -la'
alias ll='ls -la'
alias terraform_dev_plan='aws-vault exec dev_terraform -- terraform plan --parallelism=30'
alias terraform_dev_apply='aws-vault exec dev_terraform -- terraform apply --parallelism=30'
alias terraform_prod_plan='aws-vault exec prod_terraform -- terraform plan --parallelism=30'
alias terraform_prod_apply='aws-vault exec prod_terraform -- terraform apply --parallelism=30'
alias login_dev='aws --profile dev_bastion login-dev'
alias login_stg='aws --profile dev_bastion login-stg'
alias login_prod='aws --profile prod_bastion login-prod'
alias gitman='(){git add . ; git commit -m "$1" ; git push}'

function peco-select-history() {
local tac
if which tac > /dev/null; then
tac="tac"
else
tac="tail -r"
fi
BUFFER=$(\history -n 1 | \
eval $tac | \
peco --query "$LBUFFER")
CURSOR=$#BUFFER
zle clear-screen
}
zle -N peco-select-history
bindkey '^r' peco-select-history
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
source_profile=mfa

[profile prod_mfa]
role_arn=arn:aws:iam::PROD:role/ADMIN_ROLE
region=ap-northeast-1
source_profile=mfa 

[profile mfa-long-term]
region = ap-northeast-1
output = json

[profile mfa]
region = ap-northeast-1
output = json
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

login-dev  = ssm start-session --target DEVELOP_EC2_ID
login-stg  = ssm start-session --target STG_EC2_ID
login-prod = ssm start-session --target PROD_EC2_ID
```