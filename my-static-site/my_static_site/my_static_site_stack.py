from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct
from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3


class MyStaticSiteStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "MyStaticSiteQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        cfts = CloudFrontToS3(self, 'my_static_site')
        bucket = cfts.s3_bucket

        # S3へ静的ファイルをデプロイ
        s3deploy.BucketDeployment(self, "DeployWebsite",
            sources=[s3deploy.Source.asset("../site-content")],
            destination_bucket=bucket,
        )
