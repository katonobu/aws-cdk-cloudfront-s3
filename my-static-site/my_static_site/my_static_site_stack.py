import os
import boto3
from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct

def github_oidc_exists():
    """
    GitHub Actions用OIDCプロバイダーが存在するか判定。
    """
    iam_client = boto3.client('iam')
    target_url = "token.actions.githubusercontent.com"

    try:
        providers = iam_client.list_open_id_connect_providers()
        for provider in providers.get("OpenIDConnectProviderList", []):
            arn = provider["Arn"]
            details = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=arn)
            print(details.get("Url"))
            if details.get("Url").endswith(target_url):
                print(f"✅ GitHub Actions OIDCプロバイダーが存在します: {arn}")
                return arn
        print("❌ GitHub Actions OIDCプロバイダーは存在しません")
        return None
    except Exception as e:
        print("❌ 判定処理でエラー:", e)
        return None

class MyStaticSiteStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        exiprei_days = 0 # オブジェクト削除のための経過日数設定

        # S3バケット（完全非公開）
        bucket = s3.Bucket(
            self, "StaticWebBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteTaggedObjectsAfterSpecifiedDays",
                    enabled=True,
                    tag_filters={"expire": "true"},  # タグで対象を絞る
                    expiration=Duration.days(exiprei_days + 1)
                )
            ]            
        )

        # キャッシュポリシーを作成（TTLを非常に長く設定）
        cache_policy = cloudfront.CachePolicy(
            self,
            "LongLivedCachePolicy",
            cache_policy_name="LongLivedCachePolicy",
            comment="Cache forever for static files",
            default_ttl=Duration.days(3650),  # 10年間
            min_ttl=Duration.days(3650),
            max_ttl=Duration.days(3650),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True
        )

        distribution = cloudfront.Distribution(
            self, 
            "StaticWebDistribution",            
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cache_policy
            ),
            default_root_object="index.html"
        )


        # S3へ静的ファイルをデプロイ
        s3deploy.BucketDeployment(self, "DeployWebsite",
            sources=[s3deploy.Source.asset("../site-content")],
            destination_bucket=bucket,
        )

        # Lambdaコードのパス（安全な絶対パス指定）
        lambda_code_path = os.path.join(os.path.dirname(__file__), "..", "lambda")

        # Lambda関数の作成
        invalidate_lambda = _lambda.Function(self, "UpdateBktInvalidateCacheLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="update_bkt_invalidate_cache.lambda_handler",  # ファイル名.関数名
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(60),  # 60秒に設定
            environment={
                "DISTRIBUTION_ID": distribution.distribution_id  # CloudFrontのDistribution ID
            }
        )

        # S3権限付与（ListBucket, GetObject, PutObject）
        bucket.grant_read_write(invalidate_lambda)  # GetObject + PutObject
        # ListBucketは追加で明示的に付与
        invalidate_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:ListBucket"],
            resources=[bucket.bucket_arn]
        ))

        # CloudFront権限付与（CreateInvalidation）
        invalidate_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["cloudfront:CreateInvalidation"],
            resources=[distribution.distribution_arn]
        ))

        # S3イベント通知（prefixフィルタ付き）
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(invalidate_lambda),
            s3.NotificationKeyFilter(prefix="upload_done.flag")
        )

        oidc_provider_arn = github_oidc_exists()
        if oidc_provider_arn is not None:
            # GitHub Actions用IAMロールを作成（S3書き込み権限付き）
            github_role = iam.Role(self, "GitHubActionsRole",
                assumed_by=iam.FederatedPrincipal(
                    federated=oidc_provider_arn,
                    conditions={
                        "StringEquals": {
                            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                        },
                        "StringLike": {
                            "token.actions.githubusercontent.com:sub": [
                                "repo:katonobu/get-weather-charts:*",
                                "repo:katonobu/get-weather-charts:*"
                            ]
                        }
                    },
                    assume_role_action="sts:AssumeRoleWithWebIdentity"
                ),
                description="Role for GitHub Actions to deploy to S3"
            )

            # S3バケットへの書き込み権限を付与
            github_role.add_to_policy(iam.PolicyStatement(
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:DeleteObject"
                ],
                resources=[bucket.arn_for_objects("*")]
            ))
            # IAMロールのARNをCloudFormation出力
            CfnOutput(self, "GitHubRoleArn", value=github_role.role_arn)

        # CfnOutputで出力
        CfnOutput(self, "ContentsBucketName", value=bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution.distribution_id)
        CfnOutput(self, "DistributionUrl",value=f'https://{distribution.domain_name}/')
