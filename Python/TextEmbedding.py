
import json

import os
from openai import AzureOpenAI

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)

client = AzureOpenAI(
    api_key=client.get_secret("textembeddingApiKey").value,
    api_version="2024-12-01-preview",
    azure_endpoint=client.get_secret("textembeddingEndpoint").value
)
# JSONデータ（例: 法律データ）
json_data = {
    "法律名": "労働基準法",
    "条文": {
        "第一条（労働条件の原則）": [
            "労働条件は、労働者が人たるに値する生活を営むための必要を充たすべきものでなければならない。",
            "この法律で定める労働条件の基準は最低のものであるから、労働関係の当事者は、この基準を理由として労働条件を低下させてはならないことはもとより、その向上を図るように努めなければならない。"
        ],
        "第二条（労働条件の決定）": [
            "労働条件は、労働者と使用者が、対等の立場において決定すべきものである。",
            "労働者及び使用者は、労働協約、就業規則及び労働契約を遵守し、誠実に各々その義務を履行しなければならない。"
        ],
        "第三条（均等待遇）": [
            "使用者は、労働者の国籍、信条又は社会的身分を理由として、賃金、労働時間その他の労働条件について、差別的取扱をしてはならない。"
        ],
        "第四条（男女同一賃金の原則）": [
            "使用者は、労働者が女性であることを理由として、賃金について、男性と差別的取扱いをしてはならない。"
        ]
    }
}

# 法律名と条文の埋め込み生成
embeddings = {
    "法律名": json_data["法律名"],
    "条文の埋め込み": {}
}

for law_title, law_content in json_data["条文"].items():
    for idx, text in enumerate(law_content):
        response = client.embeddings.create(
            input=[text],  # リストで渡す
            model="text-embedding-3-large"
        )
        embedding = response.data[0].embedding
        embeddings["条文の埋め込み"][f"{law_title}_内容_{idx + 1}"] = {
            "原文": text,
            "埋め込み": embedding
        }
# 結果の表示（またはAzure Cosmos DBに保存）
#print(json.dumps(embeddings, indent=4))

download_path = os.path.expanduser("~/Downloads")
if not os.path.exists(download_path):
    os.makedirs(download_path)

# EmbeddingTEST.JSONとして保存
base_name = "EmbeddingTEST"
save_file_path = os.path.join(download_path, f"{base_name}.json")

with open(save_file_path, "w", encoding="utf-8") as f:
    json.dump(embeddings, f, ensure_ascii=False, indent=2)

print(f"ファイルを保存しました: {save_file_path}")