# Python と pip があるか確認
python3 --version
pip install --upgrade pip
pip --version

# Node.js と npm が必要（CDK CLIはNode製）
sudo apt-get update
sudo apt-get install -y nodejs npm

# AWS CLI インストール
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# ここで下記を聞かれる。
## AWS Access Key ID: IAMユーザーのアクセスキー
## AWS Secret Access Key: IAMユーザーのシークレットキー
## Default region name: 例 ap-northeast-1（東京リージョン）
## Default output format: json（推奨）
aws configure
aws configure list

# AWS CDK CLI インストール
npm install -g aws-cdk

# venv 作成
#python3 -m venv .venv
#source .venv/bin/activate
#pip install --upgrade pip

# CDK Python プロジェクト初期化
#mkdir my-static-site && cd my-static-site
#cdk init app --language python

cd my-static-site
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# プロジェクトのvenv環境に入っていることを確認
pip list
pip install -r requirements.txt
pip list

cdk deploy

# この先
# VS-Codeでmy-static-site を開いて、.venvを指定。

# あるいは、
# cd my-static-site
# source .venv/bin/activate

# で、
# cdk synth
# cdk deploy
