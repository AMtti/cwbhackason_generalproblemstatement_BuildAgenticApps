import streamlit as st # Streamlitを使用してWebアプリケーションを作成するためのライブラリ

import pandas as pd #データフレームを扱うためのライブラリ
from pypdf import PdfReader # PDFからテキストを抽出するためのライブラリ
import xml.etree.ElementTree as ET # XMLからテキストを抽出するためのライブラリ
import json # JSONファイルを扱うためのライブラリ

from azure.storage.blob import BlobServiceClient # Azure Blob Storageを扱うためのライブラリ

from azure.cosmos import CosmosClient, PartitionKey # Azure Cosmos DBを扱うためのライブラリ
from openai import AzureOpenAI  # OpenAIのAPIを扱うためのライブラリ
import uuid # UUIDを生成するためのライブラリ

from keys import (
     aoai_api_key, aoai_azure_endpoint,
    cosmosdb_endpoint, cosmosdb_key,
    connection_string)

#Cosmos DBの接続情報
cosmosdb_client = CosmosClient(
    cosmosdb_endpoint,
    cosmosdb_key
    )

# Azure Blob Storage の接続情報
def get_credentials_from_blob():
    # Azure Blob Storage の接続情報
    container_name = "users"
    blob_name = "users.json"
    
    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Blob からデータを取得
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)


# 認証機能
def authenticate():
    st.title("管理ユーザーログインページ")

    # Azure Blob Storage から認証情報を取得
    login_credentials = get_credentials_from_blob()

    # ユーザー入力
    username = st.text_input("IDを入力してください", key="username")
    password = st.text_input("パスワードを入力してください", type="password", key="password")
    
    # 入力値をセッションに保存
    st.session_state.current_username = username

    if st.button("ログイン"):
        # 認証フラグ
        authenticated = False

        # リスト内のユーザー情報を検索
        for login_credential in login_credentials:
            if username == login_credential["username"] and password == login_credential["password"]:
                authenticated = True
                break

        if authenticated:
            st.session_state.authenticated = True
            st.session_state.page = 'maintenance'
            #st.success("ログイン成功！")
        else:
            st.error("IDまたはパスワードが間違っています！")
            
     #サイドバー
    st.sidebar.image("../PNG/Ishigame_reading.png", caption="") 
    if st.sidebar.button("メインページに戻る"):
        st.session_state.page = 'main'
# メンテナンスページ
def maintenance_page():
    st.title("メンテナンスページ")
    # ユーザー名の表示
    st.write(f"User:{st.session_state.current_username}")
    st.write("ファイルのアップロードや削除を行うことができます。")
    st.write("ファイル追加する場合はe-Gov法令検索サイトから法律を検索し、XMLファイルをアップロードしてください。")
    st.markdown('[e-Gov法令検索サイトはこちら](https://laws.e-gov.go.jp/)')


    # データベースとコンテナーの情報
    database_name = "LegalNest"
    container_name = "Statute"

    # データベースとコンテナーのクライアント取得
    database = cosmosdb_client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    # SQLクエリを実行して結果を取得
    query = "SELECT c.種別,c.条文名,c.内容 FROM c"
    results = container.query_items(
        query=query,
        enable_cross_partition_query=True
    )
    df = pd.DataFrame(list(results))

    # DataFrameが空かどうかを確認
    if df.empty:
        # DataFrameが空の場合の処理
        
        st.write("データがありません。このままアシスタントと会話することもできますが、法律データを参照できません。")
        st.write("法律データを追加するには、メンテナンスページからXMLファイルをアップロードしてください。")
        if st.button("メンテナンスページへ移動"):
            st.session_state.page = 'maintenance'
    else:
        # DataFrameが空でない場合の処理
        value_counts_df = df['種別'].value_counts().reset_index()
        value_counts_df.columns = ['種別', '件数']  # カラム名を設定
        st.table(value_counts_df)

    # ファイル操作ボタンを追加
    col1, col2= st.columns(2)
    with col1:
        if st.button("XMLアップロード"):
            st.session_state.page = "upload_xml"
    with col2:
        if st.button("ファイル削除"):
            st.session_state.page = "delete"

    #サイドバー
    st.sidebar.image("../PNG/Ishigame_working.png", caption="")     
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"
    if st.sidebar.button("パスワード変更"):
        st.session_state.page = "changepassword"
    if st.sidebar.button("管理者ログイン"):
        st.session_state.page = "admin_login"

def change_password():
    st.title("パスワード変更")

    # Blobからデータを取得
    data = download_blob_data()
    #st.subheader("現在のユーザー")
    #df = pd.DataFrame(data)
    #st.table(df[['username']])

    # 現在ログイン中のユーザー名を取得
    username = st.session_state.current_username
    st.info(f"パスワードを変更するユーザー名: {username}")

    # 新しいパスワードの入力
    new_password = st.text_input("新しいパスワードを入力してください", type="password")

    # ボタンで変更処理
    if st.button("パスワードを変更"):
        if username and new_password.strip():
            user_found = False
            for user in data:
                if user["username"] == username:
                    user["password"] = new_password
                    user_found = True
                    break
            if user_found:
                upload_blob_data(data)
                st.success(f"ユーザー '{username}' のパスワードを変更しました！")

            else:
                st.error(f"ユーザー名 '{username}' は見つかりませんでした。")
        else:
            st.error("新しいパスワードを入力してください。")
    #サイドバー
    st.sidebar.image("../PNG/Ishigame_working.png", caption="")     
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("管理者ログイン"):
        st.session_state.page = "admin_login"

# XMLアップロードページ
def upload_xml_page():
    st.title("XMLアップロードページ")
    st.write("ファイル追加する場合はe-Gov法令検索サイトから法律を検索し、XMLファイルをアップロードしてください。")
    st.markdown('[e-Gov法令検索サイトはこちら](https://laws.e-gov.go.jp/)')

    # セッション状態の初期化
    st.session_state.uploaded_file = None

    # ファイルアップロードボタンを追加
    uploaded_file = st.file_uploader("ファイルをアップロードしてください")
    upload = False
    cancel = False
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        allowed_extensions = ['xml']
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1]

        if file_extension not in allowed_extensions:
            st.error(f"許可されていないファイル形式です。テキストファイルはテキストアップロードページからアップロードしてください。: {file_extension}")
            if st.button("テキストアップロード"):
                st.session_state.page = "upload_text"
        else:

            if file_extension == 'xml': # XMLファイル
                # XMLファイルを読み込む
                tree = ET.parse(uploaded_file)
                root = tree.getroot()
                text_content = extract_text_from_xml(root)  # ← rootを渡す
                text_str = "\n".join(text_content)  # リストを文字列に変換
                st.write("ファイル内容の一部:")
                st.text(text_str[:500])
                #xml_to_json(root) # XMLをJSONに変換して保存
                json_data = xml_to_json(root)

            # 確認ボタンとキャンセルボタンを表示
            col1, col2 = st.columns(2)
            with col1:
                if st.button("実行"):
                    upload = True

            with col2:
                if st.button("戻る"):
                    cancel = True

    if upload:
        create_embedding_and_save_to_cosmos_db(json_data)
        st.success("埋め込みを作成し、Azure Cosmos DBに保存しました。")


    if cancel:
        #st.session_state.uploaded_file = None
        #st.rerun()  # ページをリフレッシュ
        st.warning("アップロードをキャンセルしました。")
        text_str=""
        st.session_state.page = "maintenance"


    if st.session_state.uploaded_file is None:
        st.write("ファイルがアップロードされていません。")

    #サイドバー
    st.sidebar.image("../PNG/Ishigame_working.png", caption="")
    if st.sidebar.button("ファイル削除"):
        st.session_state.page = "delete" 
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"
#埋め込み作成してAzure Cosmos DBに保存する関数
def create_embedding_and_save_to_cosmos_db(json_data):
    # Cosmos DBの接続情報
    cosmos_client = CosmosClient(
        cosmosdb_endpoint, 
        cosmosdb_key
        )

    # OpenAIの設定
    textemb_client = AzureOpenAI(
        api_key=aoai_api_key,
        api_version="2024-12-01-preview",
        azure_endpoint=aoai_azure_endpoint
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

    # 条文ごとに埋め込みを生成しつつアイテムを保存
    for 条文, 内容 in json_data["条文"].items():
        # 埋め込み用のテキストを作成
        text_to_embed = " ".join(内容)  # 内容リストを単一の文字列に結合
        
        # OpenAI APIを使用して埋め込みを生成
        embedding_response = textemb_client.embeddings.create(
            input=[text_to_embed],  # リストで渡す
            model="text-embedding-3-large"
        )
        #embedding_response = response.json_data[0].embedding
        embedding = embedding_response.data[0].embedding
        # アイテムを作成
        item = {
            "id": str(uuid.uuid4()),
            "種別": json_data["法律名"],
            "条文名": 条文,
            "内容":text_to_embed ,
            "embedding": embedding       
        }
        container.upsert_item(item)  # データを挿入または更新

     
# 削除ページ
def deleteByPatition_page():
    st.title("削除ページ")
    st.write("法律名単位で削除します。")

    # データベースとコンテナーの情報
    database_name = "LegalNest"
    container_name = "Statute"

    # データベースとコンテナーのクライアント取得
    database = cosmosdb_client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    # SQLクエリを実行して結果を取得
    query = "SELECT c.種別,c.条文名,c.内容 FROM c"
    results = container.query_items(
        query=query,
        enable_cross_partition_query=True
    )
    df = pd.DataFrame(list(results))
    delete = False
    cancel = False

    if df.empty:
        # DataFrameが空の場合の処理
        
        st.write("データがありません")
        if st.button("戻る"):
            cancel = True
    else:
        # DataFrameが空でない場合の処理
        value_counts_df = df['種別'].value_counts().reset_index()
        value_counts_df.columns = ['種別', '件数']  # カラム名を設定
        st.table(df['種別'].value_counts())
        category = st.selectbox(
            '種別を選択してください',
            list(df['種別'].unique()),
            index=0
        )
        # 選択された種別に基づいてフィルタリング
        filtered_df = df[df['種別']== category]
        st.write(filtered_df[['種別', '条文名', '内容']])
        # 実行ボタンとキャンセルボタンを表示

        col1, col2 = st.columns(2)
        with col1:
            if st.button("実行"):
                delete = True

        with col2:
            if st.button("戻る"):
                cancel = True

    if delete==True:
        # パーティションキーに基づいてアイテムを削除
        delete_items(container, category)
        st.success(f"パーティションキー '{category}' のアイテムを削除しました！")
    if cancel==True:
        # メンテナンスページに戻る
        st.warning("削除をキャンセルしました。")
        st.session_state.page = "maintenance"

    #サイドバー
    st.sidebar.image("../PNG/Ishigame_cleaning.png", caption="")     
    if st.sidebar.button("XMLアップロード"):
        st.session_state.page = "upload_xml" 
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"

# 指定されたパーティションキーに基づいてアイテムを削除する関数
def delete_items(container, category):
    """
    指定されたパーティションキーに基づいてアイテムを削除する関数
    """

    # 対象アイテムを検索
    select_dei_id_query = f"SELECT c.id FROM c WHERE c.種別 = '{category}'"
    dei_id_items = container.query_items(query=select_dei_id_query, partition_key=category)

    # 該当アイテムを削除
    for item in dei_id_items:
        container.delete_item(item=item["id"], partition_key=category)
# PDFからテキストを抽出
def extract_text_from_pdf(uploaded_file):
    #uploaded_file.seek(0)  # ストリームの先頭に戻す
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# XMLからテキストを抽出
def extract_text_from_xml(element):
    text_content = []
    if element.text:
        text_content.append(element.text.strip())
    for child in element:
        text_content.extend(extract_text_from_xml(child))
    return text_content

# XMLから抽出したテキストをJSONに変換して保存
def xml_to_json(root):
    # 法律名取得
    lawTitle = root.find('.//LawTitle').text

    # すべての条文を処理
    articles_dict = {}
    for article in root.findall('.//MainProvision//Article'):
        article_title = article.findtext('ArticleTitle') or ""
        article_caption = article.findtext('ArticleCaption') or ""
        key = f"{article_title}{article_caption}"

        # パラグラフセンテンスを抽出
        sentences = []
        for para in article.findall('.//ParagraphSentence'):
            for sentence in para.findall('Sentence'):
                if sentence.text:
                    sentences.append(sentence.text.strip())
        articles_dict[key] = sentences

    for article in root.findall('.//SupplProvision//Article'):
        supplProvision_Label = "附則_"
        article_title = article.findtext('ArticleTitle') or ""
        article_caption = article.findtext('ArticleCaption') or ""
        key = f"{supplProvision_Label}{article_title}{article_caption}"

        # パラグラフセンテンスを抽出
        sentences = []
        for para in article.findall('.//ParagraphSentence'):
            for sentence in para.findall('Sentence'):
                if sentence.text:
                    sentences.append(sentence.text.strip())
        articles_dict[key] = sentences


    # JSONデータ作成
    json_data = {
        "法律名": lawTitle,
        "条文": articles_dict

    }

    return json_data


#管理者の認証情報を取得
def get_admin_credentials_from_blob():
    # Azure Blob Storage の接続情報
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
    admin_credentials = get_admin_credentials_from_blob()

    # ユーザー入力
    username = st.text_input("IDを入力してください", key="username")
    password = st.text_input("パスワードを入力してください", type="password", key="password")

    # 入力値をセッションに保存
    st.session_state.current_adminname = username

    if st.button("ログイン"):
        # 認証フラグ
        authenticated = False

        # リスト内のユーザー情報を検索
        for admin_credential in admin_credentials:
            if username == admin_credential["username"] and password == admin_credential["password"]:
                authenticated = True
                break

        if authenticated:
            st.session_state.authenticated = True                
            st.session_state.page = "admin"
        else:
            st.error("IDまたはパスワードが間違っています！")

    # サイドバー
    st.sidebar.image("../PNG/Ishigame_working.png", caption="")
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = 'maintenance'
# 管理者ページ
def admin():
    st.title("管理者ページ")
    st.write(f"User: {st.session_state.current_adminname}")
    st.write("このページでは、ユーザーの追加や削除を行うことができます。")
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
    st.sidebar.image("../PNG/Ishigame_working.png", caption="キャプションをここに書く")

    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = 'maintenance'

# Blobデータをダウンロード
def download_blob_data():
    container_name = "users"
    blob_name = "users.json"
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# Blobデータをアップロード
def upload_blob_data(data):
    container_name = "users"
    blob_name = "users.json"

    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(json.dumps(data), overwrite=True)

# ユーザー追加
def add_user():
    st.title("管理ユーザー追加")

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
        if new_username.strip() and new_password.strip():
            # ここで重複チェック
            if any(user["username"] == new_username for user in data):
                st.error(f"ユーザー名 '{new_username}' は既に存在します。別のユーザー名を入力してください。")
            else:
                new_user = {"username": new_username, "password": new_password}
                data.append(new_user)
                upload_blob_data(data)
                st.success(f"ユーザー '{new_username}' を追加しました！")

                # 更新後のデータを表示
                st.subheader("更新後のユーザー")
                df_updated = pd.DataFrame(data)
                st.table(df_updated[['username']])
        else:
            st.error("ユーザー名とパスワードを入力してください。")

    #サイドバー
    st.sidebar.image("../PNG/Ishigame_working.png", caption="")
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
    st.title("管理ユーザー削除）")

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
    st.sidebar.image("../PNG/Ishigame_working.png", caption="キャプションをここに書く")
    if st.sidebar.button("ユーザー追加"):
        st.session_state.page = "add_User"   
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = 'maintenance' 
