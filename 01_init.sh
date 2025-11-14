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

# AWS CDK CLI インストール
npm install -g aws-cdk

# venv 作成
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# CDK Python プロジェクト初期化
mkdir my-static-site && cd my-static-site
cdk init app --language python

source .venv/bin/activate
pip install --upgrade pip

# プロジェクトのvenv環境に入っていることを確認
pip list

# AWS Solutions Constructs の CloudFront-S3 パターン
# requiremts.txtを更新したのでインストールされてるはず。
# pip install aws_solutions_constructs.aws_cloudfront_s3

# 必要なパッケージがインストールされたことを確認
#pip list

# AWS認証情報を設定（Codespacesに環境変数で設定）
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_DEFAULT_REGION=ap-northeast-1

# CDK bootstrap（アカウント、リージョンに対して1回やればよい）
#cdk bootstrap

cdk synth

#cdk deploy

# aws s3 cp ../index.html s3://<your-bucket-name>