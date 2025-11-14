import os
import json
import boto3
import requests
import time
import tempfile


stack_name = 'MyStaticSiteStack'
deploy_json_file_name = "cdk-outputs.json"
deploy_info_key = "MyStaticSiteStack"
compare_s3_http_file_name = "index.html"
dynamic_file_name = "directory_list.json"
invalidate_trigger_file_name = "upload_done.flag"


import boto3

def delete_bucket(s3, bucket_name):
    # まだバージョン付きのバケット削除に失敗する。
    try:
        # バケットを削除する前に、中身を空にする必要があります
        # まずオブジェクト一覧を取得
        objects = s3.list_objects_v2(Bucket=bucket_name)

        if 'Contents' in objects:
            print("バケット内のオブジェクトを削除中...")
            for obj in objects['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
            print("✅ バケット内のオブジェクトを削除しました")

        time.sleep(3)
        # バケットを削除
        s3.delete_bucket(Bucket=bucket_name)
        print(f"✅ バケット '{bucket_name}' を削除しました")

    except Exception as e:
        print("❌ バケット削除に失敗しました:", e)

def main():
    result = True

    # -----------------------------
    # 1. CDK Outputs JSONを読み込み
    # -----------------------------
    site_info_file_path_name = os.path.join(os.path.dirname(__file__), "..", deploy_json_file_name)
    with open(site_info_file_path_name, 'r', encoding='utf-8') as f:
        site_info = json.load(f)
    
    stack_outputs = site_info.get(deploy_info_key, {})
    c_bucket_name = stack_outputs.get("ContentsBucketName")
    cflog_bucket_name = stack_outputs.get("CloudFrontLoggingBucketName")
    s3log_bucket_name = stack_outputs.get("S3LoggingBucketName")

    print(f"ContentsBucketName: {c_bucket_name}")
    print(f"CloudFrontLoggingBucketName: {cflog_bucket_name}")
    print(f"S3LoggingBucketName: {s3log_bucket_name}")

    s3 = boto3.client('s3')
    # バケット一覧を取得
    response = s3.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]

    for bucket_name in [c_bucket_name, cflog_bucket_name, s3log_bucket_name]:
        if bucket_name in bucket_names:
            print(f"バケット '{bucket_name}' が存在します。削除を開始します...")
            delete_bucket(s3, bucket_name)
        elif bucket_name.startswith('-'.join(bucket_name.split("-")[:2])):
            print(f"バケット '{bucket_name}' が存在します。削除を開始します...")
            delete_bucket(s3, bucket_name)
        else:
            print(f"バケット '{bucket_name}' は存在しません。")


if __name__ == "__main__":
    main()
