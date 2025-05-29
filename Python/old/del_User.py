from azure.storage.blob import BlobServiceClient
import json
import pandas as pd
import streamlit as st

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)



def get_credentials_from_blob():
    # Azure Blob Storage の接続情報
    connection_string = client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"
    
    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Blob からデータを取得
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# Blobデータをダウンロード
def download_blob_data():
    # Azure Blob Storage の接続情報
    connection_string = client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"
    
    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# Blobデータをアップロード
def upload_blob_data(data):
    # Azure Blob Storage の接続情報
    connection_string = client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"

    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(json.dumps(data), overwrite=True)

# 指定したユーザーを削除
def delete_user(data, username_to_remove):
    updated_data = [user for user in data if user["username"] != username_to_remove]
    return updated_data

# ユーザー削除
def del_user():
    st.title("Blobデータの編集（削除機能付き）")

    # Blobからデータを取得して表示
    data = download_blob_data()
    st.subheader("現在のユーザーデータ")
    df = pd.DataFrame(data)
    st.table(df[['username']])

    # 削除するユーザー名の入力
    username_to_remove = st.text_input("削除したいユーザー名を入力してください")

    if st.button("削除"):
        if username_to_remove.strip():  # 入力が空でないことを確認
            # データを削除
            updated_data = delete_user(data, username_to_remove)

            if len(updated_data) < len(data):  # ユーザーが削除された場合
                upload_blob_data(updated_data)  # 更新されたデータをアップロード
                st.success(f"ユーザー '{username_to_remove}' を削除しました！")

                # 更新後のデータを表示
                st.subheader("更新後のユーザーデータ")
                df_updated = pd.DataFrame(updated_data)
                st.table(df_updated[['username']])
            else:
                st.warning(f"ユーザー '{username_to_remove}' は見つかりませんでした。")
        else:
            st.error("ユーザー名を入力してください。")

if __name__ == "__main__":
    del_user()
