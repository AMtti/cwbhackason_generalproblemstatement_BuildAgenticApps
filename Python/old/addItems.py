from azure.cosmos import CosmosClient, PartitionKey
import uuid
import openai
from openai import AzureOpenAI

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)


# Cosmos DBの接続情報をKey Vaultから取得
# Cosmos DBへの接続設定
endpoint = secret_client.get_secret("cosmosdbendpoint").value
key = secret_client.get_secret("cosmosdbkey").value
cosmos_client = CosmosClient(endpoint, key)
# OpenAI APIの接続設定
textemb_client = AzureOpenAI(
    api_key=secret_client.get_secret("textembeddingApiKey").value,
    api_version="2024-12-01-preview",
    azure_endpoint=secret_client.get_secret("textembeddingEndpoint").value
)

# データベースとコンテナーの設定
database_name = "LegalNest"
container_name = "Statute"

# データベースとコンテナーの作成または取得
database = cosmos_client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/種別")  # パーティションキーを設定
)

# JSONデータ（例）
data = {
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
        ]
    }
}

# 条文ごとに埋め込みを生成しつつアイテムを保存
for 条文, 内容 in data["条文"].items():
    # 埋め込み用のテキストを作成
    text_to_embed = " ".join(内容)  # 内容リストを単一の文字列に結合

    # OpenAI APIを使用して埋め込みを生成
    embedding_response = textemb_client.embeddings.create(
        input=[text_to_embed],  # リストで渡す
        model="text-embedding-3-large"
    )
    #embedding_response = response.data[0].embedding
    embedding = embedding_response.data[0].embedding
    # アイテムを作成
    item = {
        "id": str(uuid.uuid4()),
        "種別": data["法律名"],
        "条文名": 条文,
        "内容":text_to_embed ,
        "embedding": embedding       
    }
    container.upsert_item(item)  # データを挿入または更新

print("すべての条文をCosmos DBに保存しました！")


