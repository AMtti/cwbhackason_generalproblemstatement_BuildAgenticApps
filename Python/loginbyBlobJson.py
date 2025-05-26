from azure.storage.blob import BlobServiceClient
import streamlit as st
import json
#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# 認証クライアントを作成
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)

st.session_state.page = 'login'

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

def authenticate():
    st.title("ログインページ")

    # Azure Blob Storage から認証情報を取得
    credentials = get_credentials_from_blob()

    # ユーザー入力
    username = st.text_input("IDを入力してください", key="username")
    password = st.text_input("パスワードを入力してください", type="password", key="password")

    if st.button("ログイン"):
        # 認証フラグ
        authenticated = False

        # リスト内のユーザー情報を検索
        for credential in credentials:
            if username == credential["username"] and password == credential["password"]:
                authenticated = True
                break

        if authenticated:
            st.session_state.authenticated = True
            st.session_state.page = 'maintenance'
            st.success("ログイン成功！")
        else:
            st.error("IDまたはパスワードが間違っています！")

    # サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")
    if st.sidebar.button("メインページに戻る"):
        st.session_state.page = 'main'

if st.session_state.page == 'login':
    authenticate()