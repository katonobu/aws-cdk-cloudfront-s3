import os
import json
import boto3
import datetime
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # イベントからバケット名とオブジェクトキーを取得
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    # 完了通知ファイルか確認
    if object_key != 'upload_done.flag':
        logger.info(f"Not a completion flag: {object_key}")
        return {"status": "ignored"}

    logger.info(f"Completion flag detected in bucket: {bucket_name}")

    s3 = boto3.client('s3')

    # 環境変数からdistribution IDを取得
    distribution_id = os.environ['DISTRIBUTION_ID']    

    # バケット内のオブジェクト一覧を取得
    directories = set()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            # ディレクトリ名を抽出（"/"で分割）
            if '/' in key:
                dir_name = key.split('/')[0]
                directories.add(dir_name)

    dir_list = list(sorted(directories, reverse=True))
    # 一覧ファイルを作成/S3にアップロード
    dirlist_path = os.path.join('/tmp', 'directory_list.json')
    with open(dirlist_path, 'w', encoding='utf-8') as f:
        json.dump(dir_list, f, indent=2, ensure_ascii=False)

    # S3にアップロード
    s3.upload_file(
        Filename=dirlist_path,
        Bucket=bucket_name,
        Key='directory_list.json',
        ExtraArgs={'ContentType': 'application/json; charset=utf-8'}
    )
    logger.info(f"Updated directory list in {bucket_name}/directory_list.json")

    ## CloudFrontのキャッシュを無効化
    cloudfront = boto3.client('cloudfront')

    # CloudFrontキャッシュの無効化
    response = cloudfront.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': ['/directory_list.json']
            },
            'CallerReference': str(datetime.datetime.now().timestamp())
        }
    )

    return {"status": "success", "directories": dir_list}
