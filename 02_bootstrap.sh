# AWS認証情報を設定（Codespacesに環境変数で設定）
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_xxx
export AWS_DEFAULT_REGION=ap-northeast-1

# CDK bootstrap（初回のみ）
cdk bootstrap

# デプロイ
cdk deploy