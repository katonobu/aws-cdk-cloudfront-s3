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


def wait_for_stack_complete(stack_name, interval=10):
    cf = boto3.client('cloudformation')
    while True:
        response = cf.describe_stacks(StackName=stack_name)
        stack_status = response['Stacks'][0]['StackStatus']
        print(f"現在のステータス: {stack_status}")

        if stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            print("✅ スタックのデプロイが完了しました")
            break
        elif stack_status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
            print("❌ スタックのデプロイに失敗しました")
            break
        time.sleep(interval)

def main():
    result = True

    # 事前準備
    ## スタックのデプロイ完了を待機
    wait_for_stack_complete(stack_name)

    # -----------------------------
    # 1. CDK Outputs JSONを読み込み
    # -----------------------------
    site_info_file_path_name = os.path.join(os.path.dirname(__file__), "..", deploy_json_file_name)
    with open(site_info_file_path_name, 'r', encoding='utf-8') as f:
        site_info = json.load(f)
    
    stack_outputs = site_info.get(deploy_info_key, {})
    bucket_name = stack_outputs.get('ContentsBucketName')
    distribution_id = stack_outputs.get('DistributionId')
    distribution_url = stack_outputs.get('DistributionUrl')

    print(f"Bucket: {bucket_name}")
    print(f"Distribution ID: {distribution_id}")
    print(f"CloudFront URL: {distribution_url}")

    # CloudFrontクライアントを作成
    cloudfront = boto3.client('cloudfront')

    ## 1回もキャッシュクリアしていなければキャッシュクリアする。
    # キャッシュ無効化リクエスト一覧を取得
    response = cloudfront.list_invalidations(DistributionId=distribution_id)
    while 0 == len(response.get('InvalidationList', {}).get('Items', [])):
        s3.put_object(Bucket=bucket_name, Key=invalidate_trigger_file_name, Body="", ContentType='binary/octet-stream')
        print("✅ 初回キャッシュInvalidateトリガのファイルを更新しました")
        print("キャッシュクリア待機中...")
        time.sleep(30)  # 実際はInvalidation完了をポーリングするのがベスト
        response = cloudfront.list_invalidations(DistributionId=distribution_id)
    print("✅ キャッシュ無効化リクエストが存在します")

    # -----------------------------
    # 2. バケットの存在確認
    # -----------------------------
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
        print("✅ バケットは存在します")
    except Exception as e:
        print("❌ バケットが存在しません:", e)
        result = False
        exit(1)

    # -----------------------------
    # 3. URLにアクセスして内容確認
    # -----------------------------
    url = f"{distribution_url}{compare_s3_http_file_name}"

    response = requests.get(url)
    if response.status_code == 200:
        original_content = response.text
        print("✅ URLアクセス成功")
        print("現在の内容:", original_content[:100], "...")
    else:
        print("❌ URLアクセス失敗:", response.status_code)
        result = False
        exit(1)

    # -----------------------------
    # 4. バケットのファイルを書き換える前にhttps経由の内容を確認
    # -----------------------------
    url = f"{distribution_url}{dynamic_file_name}"
    response_before_update = requests.get(url)
    print("書き換え前のURL内容:", response_before_update.text[:100], "...")

    # -----------------------------
    # 4. バケットのファイルを書き換える
    # -----------------------------
    new_content = '[{"hoge": "fuga"}]'
    s3.put_object(Bucket=bucket_name, Key=dynamic_file_name, Body=new_content, ContentType='application/json')
    print("✅ バケットのファイルを更新しました")
    print("バケットのファイルの新しい内容:", new_content)

    # -----------------------------
    # 5. キャッシュ確認（Invalidate前）
    # -----------------------------
    time.sleep(5)  # 少し待ってから確認
    url = f"{distribution_url}{dynamic_file_name}"
    response_after_update = requests.get(url)

    print("Invalidate前のURL内容:", response_after_update.text[:100], "...")
    if response_after_update.text != new_content:
        print("✅ 書き換えたファイルが見えていません(キャッシュが効いています）")
        if response_after_update.text == response_before_update.text:
            print("✅ 書き換え前のhttpsアクセスの内容と同じです(キャッシュが効いています）")
        else:
            print("❌ 書き換え前のhttpsアクセスの内容と異なります")
            result = False
    else:
        print("⚠ キャッシュが効いていない（新しい内容）")
        result = False

    # キャッシュ無効化リクエスト一覧を取得
    response = cloudfront.list_invalidations(DistributionId=distribution_id)
    # 結果を表示
    sorted_items = sorted([item for item in response.get('InvalidationList', {}).get('Items', [])], key=lambda x: x['CreateTime'], reverse=True)
    prev_latest = sorted([item for item in response.get('InvalidationList', {}).get('Items', [])], key=lambda x: x['CreateTime'], reverse=True)[0]
    print(f'   キャッシュ無効化前最終リクエスト作成時間:{prev_latest["CreateTime"]}')

    # -----------------------------
    # 6. CloudFrontキャッシュをInvalidate
    # -----------------------------
    s3.put_object(Bucket=bucket_name, Key=invalidate_trigger_file_name, Body="", ContentType='binary/octet-stream')
    print("✅ キャッシュInvalidateトリガのファイルを更新しました")

    # -----------------------------
    # 7. Invalidate後の確認
    # -----------------------------
    print("キャッシュクリア待機中...")
    time.sleep(30)  # 実際はInvalidation完了をポーリングするのがベスト

    url = f"{distribution_url}{dynamic_file_name}"
    response_after_invalidate = requests.get(url)
    print("Invalidate後のURL内容:", response_after_invalidate.text[:100], "...")
    if response_after_invalidate.text != new_content:
        print("✅ 古い内容が更新されています")
        with tempfile.TemporaryDirectory() as temp_dir:
            download_content_file_path_name = os.path.join(temp_dir, f'downloaded_{dynamic_file_name}')
            s3.download_file(bucket_name, dynamic_file_name, download_content_file_path_name)
            with open(download_content_file_path_name, 'r', encoding='utf-8') as f:
                downloaded_content = f.read()
            if downloaded_content == response_after_invalidate.text:
                print("✅ バケットの内容とhttp経由の内容が一致します")

                # キャッシュ無効化リクエスト一覧を取得
                response = cloudfront.list_invalidations(DistributionId=distribution_id)
                post_latest = sorted([item for item in response.get('InvalidationList', {}).get('Items', [])], key=lambda x: x['CreateTime'], reverse=True)[0]
                print(f'   キャッシュ無効化後最終リクエスト作成時間:{post_latest["CreateTime"]}')
                if prev_latest.get('Id') != post_latest.get('Id'):
                    print("✅ 新しいキャッシュ無効化リクエストが確認できました")
                else:
                    print("❌ 新しいキャッシュ無効化リクエストが確認できません")
                    result = False
            else:
                print("❌ バケットの内容とhttp経由の内容が一致しません")
                result = False
    else:
        print("❌ まだ古い内容です（Invalidation未完了の可能性）")
        result = False
    return result


if __name__ == "__main__":
    result = main()
    print("+----------------------------------------------+")
    print("|                                              |")
    if result:
        print("|         ✅ All Tests Passed! ✅             |")
    else:
        print("|           ❌ Tests Failed ❌                |")
    print("|                                              |")
    print("+----------------------------------------------+")
