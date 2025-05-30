from azure.cosmos import CosmosClient
import pandas as pd
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
client = CosmosClient(
    secret_client.get_secret("cosmosdbendpoint").value,
    secret_client.get_secret("cosmosdbkey").value
    )

# データベースとコンテナーの情報
database_name = "LegalNest"
container_name = "Statute"

# データベースとコンテナーのクライアント取得
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# SQLクエリを実行して結果を取得
query = "SELECT c.種別,c.条文名,c.内容 FROM c"
results = container.query_items(
    query=query,
    enable_cross_partition_query=True
)
df = pd.DataFrame(list(results))


st.table(df['種別'].value_counts())
category = st.selectbox(
    '種別を選択してください',
    list(df['種別'].unique()),
    index=0
)
# 選択された種別に基づいてフィルタリング

filtered_df = df[df['種別']== category]
st.table(filtered_df[['種別', '条文名', '内容']][0:5])