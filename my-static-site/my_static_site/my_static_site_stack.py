import os
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct
from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3
from aws_solutions_constructs.aws_s3_lambda import S3ToLambda
from aws_cdk import aws_iam as iam

class MyStaticSiteStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CloudFront + S3の構成を作成
        cloudfront_s3 = CloudFrontToS3(self, 'my_static_site')
        bucket = cloudfront_s3.s3_bucket
        distribution_id = cloudfront_s3.cloud_front_web_distribution.distribution_id

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
                "DISTRIBUTION_ID": distribution_id  # CloudFrontのDistribution ID
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
            resources=[cloudfront_s3.cloud_front_web_distribution.distribution_arn]
        ))

        # S3イベント通知（prefixフィルタ付き）
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(invalidate_lambda),
            s3.NotificationKeyFilter(prefix="upload_done.flag")
        )

        # CfnOutputで出力
        CfnOutput(self, "ContentsBucketName", value=bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution_id)
        CfnOutput(self, "DistributionUrl",value=f'https://{cloudfront_s3.cloud_front_web_distribution.domain_name}/')
        CfnOutput(self, "S3LoggingBucketName", value=cloudfront_s3.s3_logging_bucket.bucket_name)
        CfnOutput(self, "CloudFrontLoggingBucketName", value=cloudfront_s3.cloud_front_logging_bucket.bucket_name)