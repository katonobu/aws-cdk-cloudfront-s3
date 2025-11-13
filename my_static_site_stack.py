import os
import json
from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3
from aws_cdk import Stack
from constructs import Construct

class MyStaticSiteStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "MyStaticSiteQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        result = CloudFrontToS3(self, 'my_static_site')