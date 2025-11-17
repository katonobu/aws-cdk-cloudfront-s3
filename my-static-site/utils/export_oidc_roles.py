import boto3
import json

def export_oidc_and_roles(output_file="oidc_roles.json"):
    iam = boto3.client('iam')

    result = {
        "oidc_providers": [],
        "iam_roles": []
    }

    # 1. OIDCプロバイダー一覧を取得
    oidc_list = iam.list_open_id_connect_providers()
    for provider in oidc_list.get("OpenIDConnectProviderList", []):
        arn = provider["Arn"]
        details = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=arn)
        result["oidc_providers"].append({
            "arn": arn,
            "url": details.get("Url"),
            "client_ids": details.get("ClientIDList"),
            "thumbprints": details.get("ThumbprintList"),
            "create_date": details.get("CreateDate").isoformat() if details.get("CreateDate") else None
        })

    # 2. IAMロール一覧を取得
    roles = iam.list_roles()
    for role in roles.get("Roles", []):
        role_name = role["RoleName"]
        role_details = iam.get_role(RoleName=role_name)
        # 信頼ポリシーを含める
        assume_policy = role_details["Role"].get("AssumeRolePolicyDocument", {})
        for st in assume_policy.get("Statement", []):
            if st.get("Action") == "sts:AssumeRoleWithWebIdentity":
                result["iam_roles"].append({
                    "role_name": role_name,
                    "arn": role["Arn"],
                    "assume_role_policy": assume_policy,
                    "create_date": role["CreateDate"].isoformat() if role.get("CreateDate") else None
                })
                break

    # 3. JSONファイルに保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"✅ OIDCプロバイダーとIAMロール情報を '{output_file}' に保存しました")

if __name__ == "__main__":
    export_oidc_and_roles()