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

# ページ遷移用のセッション状態を初期化
if 'page' not in st.session_state:
    st.session_state.page = 'admin_login'  # 最初はログインページからスタート

#ユーザーの認証情報を取得
def get_credentials_from_blob():
    # Azure Blob Storage の接続情報
    connection_string = client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"
    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Blob からユーザーデータを取得
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

#管理者の認証情報を取得
def get_admin_credentials_from_blob():
    # Azure Blob Storage の接続情報
    connection_string = client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_admin_name = "admi.json"   
    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_admin_client = blob_service_client.get_blob_client(container=container_name, blob=blob_admin_name)
    
    # Blob からユーザーデータを取得
    blob_admin_data = blob_admin_client.download_blob().readall()
    return json.loads(blob_admin_data)

#管理者ログインページ
def authenticate_admin():
    st.title("管理者ページログイン")

    # Azure Blob Storage から認証情報を取得
    credentials = get_admin_credentials_from_blob()

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
            st.session_state.page = "admin"
        else:
            st.error("IDまたはパスワードが間違っています！")

    # サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = 'maintenance'
# 管理者ページ
def admin():
    st.title("管理者ページ")

    # 認証済みか確認
    if not st.session_state.get('authenticated', False):
        st.error("ログインが必要です。")
        return

    # Blobからデータを取得
    data = get_credentials_from_blob()
    st.subheader("現在のユーザー")
    df = pd.DataFrame(data)
    st.table(df[['username']])
    # 確認ボタンとキャンセルボタンを表示
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ユーザー追加"):
            st.session_state.page = "add_User"

    with col2:
        if st.button("ユーザー削除"):
            st.session_state.page = "del_User"
    # サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")

    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = 'maintenance'

# Blobデータをダウンロード
def download_blob_data():
    connection_string = client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# Blobデータをアップロード
def upload_blob_data(data):
    connection_string = client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"

    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(json.dumps(data), overwrite=True)

# ユーザー追加
def add_user():
    st.title("Blobデータの編集（ユーザー追加）")

    # Blobからデータを取得
    data = download_blob_data()
    st.subheader("現在のユーザー")
    df = pd.DataFrame(data)
    st.table(df[['username']])

    # ユーザー入力
    st.subheader("新しいユーザーを追加")
    new_username = st.text_input("ユーザー名を入力してください")
    new_password = st.text_input("パスワードを入力してください", type="password")

    # ボタンで追加処理
    if st.button("ユーザーを追加"):
        if new_username.strip() and new_password.strip():  # 入力が空白でないことを確認
            new_user = {"username": new_username, "password": new_password}
            data.append(new_user)  # 新しいユーザーを追加
            upload_blob_data(data)  # 更新後のデータをアップロード
            st.success(f"ユーザー '{new_username}' を追加しました！")

            # 更新後のデータを表示
            st.subheader("更新後のユーザー")
            df_updated = pd.DataFrame(data)
            st.table(df_updated[['username']])
        else:
            st.error("ユーザー名とパスワードを入力してください。")
    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")
    if st.sidebar.button("ユーザー削除"):
        st.session_state.page = "del_User"    
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = 'maintenance'

# 指定したユーザーを削除
def delete_user(data, username_to_remove):
    updated_data = [user for user in data if user["username"] != username_to_remove]
    return updated_data

# ユーザー削除
def del_user():
    st.title("Blobデータの編集（削除機能）")

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
    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")
    if st.sidebar.button("ユーザー追加"):
        st.session_state.page = "add_User"   
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = 'maintenance' 

# ページ遷移
if st.session_state.page == 'add_User':
    add_user()
elif st.session_state.page == 'del_User':
    del_user()
elif st.session_state.page == 'admin_login':
    authenticate_admin()
elif st.session_state.page == 'admin':
    admin()
#elif st.session_state.page == 'maintenance' and st.session_state.authenticated:
#    maintenance_page()
