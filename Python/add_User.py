from azure.storage.blob import BlobServiceClient
import json
import pandas as pd
import streamlit as st

# Azure Blob Storageの接続情報
connection_string = "DefaultEndpointsProtocol=https;AccountName=accountcwbhackason2025am;AccountKey=77O3OXG8TtgSjVhUX8cEQ5xwpFte1J45U0TGD1MgQjL+bwl1zCprD9gdev7Gq1ZgeKhB8jy/IabQ+AStH7rR5g==;EndpointSuffix=core.windows.net"
container_name = "users"
blob_name = "users.json"

# Blobデータをダウンロード
def download_blob_data():
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# Blobデータをアップロード
def upload_blob_data(data):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(json.dumps(data), overwrite=True)

# Streamlitを使ったデータ編集
def main():
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

if __name__ == "__main__":
    main()
