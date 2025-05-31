from azure.cosmos import CosmosClient
from openai import AzureOpenAI
import json
import re

import streamlit as st

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Cosmos DBの接続情報
cosmosDB_client = CosmosClient(
    secret_client.get_secret("cosmosdbendpoint").value,
    secret_client.get_secret("cosmosdbkey").value
    )
# データベースとコンテナーの情報
database_name = "LegalNest"
container_name = "Statute"


# Azure OpenAI クライアントの設定
textembedding_client = AzureOpenAI(
    api_key=secret_client.get_secret("textembeddingApiKey").value,
    api_version="2024-12-01-preview",
    azure_endpoint=secret_client.get_secret("textembeddingEndpoint").value
)


# 入力テキスト
text = "労働基準法第六十五条第一項の規定による休業"

# 類似検索に使用するベクトル埋め込みデータ
response = textembedding_client.embeddings.create(
    input=text,
    model="text-embedding-3-large"
)
query_embedding = response.data[0].embedding

# Cosmos Client の作成
database = cosmosDB_client.get_database_client(database_name)
container = database.get_container_client(container_name)

# クエリの作成
# 「第〇〇条」を抽出
match = re.search(r"(第.+?条)", text)
print(match)
article = match.group(1) if match else None
print(article)
if article:
    for item in container.query_items(
        query="""
            SELECT c.条文名, c.内容
            FROM c
            WHERE c.種別 = @type AND CONTAINS(c.条文名, @article)
        """,
        parameters=[
            {"name": "@article", "value": article},
            {"name": "@type", "value": "雇用の分野における男女の均等な機会及び待遇の確保等に関する法律"}
        ],
        enable_cross_partition_query=True
    ):
        print(json.dumps(item, indent=2, ensure_ascii=False))
else:
    print("条文名が見つかりませんでした")

# Query for items 
for item in container.query_items(
    query="""
        SELECT TOP 1 c.条文名, c.内容, VectorDistance(c.embedding, @embedding) AS SimilarityScore
        FROM c
        WHERE c.種別 = @type
        ORDER BY VectorDistance(c.embedding, @embedding)
    """,
    parameters=[
        {"name": "@embedding", "value": query_embedding},
        {"name": "@type", "value": "雇用の分野における男女の均等な機会及び待遇の確保等に関する法律"}
    ],
    enable_cross_partition_query=True
):
    print(json.dumps(item, indent=2, ensure_ascii=False))