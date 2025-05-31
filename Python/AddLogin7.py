import streamlit as st
import pandas as pd #データフレームを扱うためのライブラリ
import os # ファイルアップロードと削除のためのライブラリ
import asyncio # 非同期処理を行うためのライブラリ
from pypdf import PdfReader # PDFからテキストを抽出するためのライブラリ
import xml.etree.ElementTree as ET # XMLからテキストを抽出するためのライブラリ
import json # JSONファイルを扱うためのライブラリ
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions import kernel_function

from azure.storage.blob import BlobServiceClient # Azure Blob Storageを扱うためのライブラリ

from azure.cosmos import CosmosClient, PartitionKey # Azure Cosmos DBを扱うためのライブラリ
from openai import AzureOpenAI  # OpenAIのAPIを扱うためのライブラリ

import uuid # UUIDを生成するためのライブラリ

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential as key_DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
credential = key_DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Cosmos DBの接続情報
cosmosdb_client = CosmosClient(
    secret_client.get_secret("cosmosdbendpoint").value,
    secret_client.get_secret("cosmosdbkey").value
    )


def get_credentials_from_blob():
    # Azure Blob Storage の接続情報
    connection_string = secret_client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"
    
    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Blob からデータを取得
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# セッション状態を初期化
if 'page' not in st.session_state:
    st.session_state.page = 'main'

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# 認証機能
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
            #st.success("ログイン成功！")
        else:
            st.error("IDまたはパスワードが間違っています！")
            
     #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く") 
    if st.sidebar.button("メインページに戻る"):
        st.session_state.page = 'main'

# メインページ
def main_page():
    st.title("メインページ")
    st.write("これはメインページです！")

    user_input = st.text_input("お困りごとを教えてください。", value="ここにテキストを入力してください。")
    if user_input:
        st.write(f"あなたが入力した内容: {user_input}")
    
    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("メンテナンスページへ移動"):
        st.session_state.page = 'login'

# メンテナンスページ
def maintenance_page():
    st.title("メンテナンスページ")
    st.write("現在メンテナンス中です。")


    # ファイル操作ボタンを追加

    col1, col2= st.columns(2)
    with col1:
        if st.button("XMLアップロード"):
            st.session_state.page = "upload_xml"
    with col2:
        if st.button("テキスト入力"):
            st.session_state.page = "input_text" 
    col3,col4= st.columns(2) 
    with col3:
        if st.button("テキストアップロード"):
            st.session_state.page = "upload_text"
    with col4:
        if st.button("ファイル削除"):
            st.session_state.page = "delete"
    # 管理者メニューボタンを追加

    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"
    if st.sidebar.button("管理者ログイン"):
        st.session_state.page = "admin_login"

# XMLアップロードページ
def upload_xml_page():
    st.title("XMLアップロードページ")
    st.write("現在メンテナンス中です。")

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
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")
    if st.sidebar.button("テキスト入力"):
        st.session_state.page = "input_text"      
    if st.sidebar.button("テキストアップロード"):
        st.session_state.page = "upload_text"   
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
        secret_client.get_secret("cosmosdbendpoint").value, 
        secret_client.get_secret("cosmosdbkey").value
        )

    # OpenAIの設定
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

#テキストファイルのアップロードページ
def upload_text_page():
    st.title("テキストファイルアップロードページ")
    st.write("現在メンテナンス中です。")

    # セッション状態の初期化
    st.session_state.uploaded_file = None

    # キー入力用のテキストボックスを追加
    key_value = st.text_input("キーを入力してください")
    st.write(f"入力されたキー: {key_value}")

    # ファイルアップロードボタンを追加
    uploaded_file = st.file_uploader("ファイルをアップロードしてください。含まれる文字列を値として格納します")
    upload = False
    cancel = False
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        allowed_extensions = ['txt', 'csv', 'pdf']
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1]

        if file_extension not in allowed_extensions:
            # XMLファイルはここでは扱わない
            if file_extension == 'xml':
                st.error("XMLファイルアップロードページでアップロードしてください。")
                if st.button("XMLファイルアップロード"):
                   st.session_state.page = "upload_xml"


            else:
                st.error(f"許可されていないファイル形式です: {file_extension}")
        else:
            if file_extension == 'pdf': #PDF
                text = extract_text_from_pdf(uploaded_file) # PDFからテキストを抽出
                # テキストファイルに書き込む
                if text == "":
                    st.warning("PDFからテキストを抽出できませんでした。PDFが認識できない形式である可能性があります。.txt 若しくは .csv, .xml形式で再試行してください。")
                else:
                    st.write("ファイル内容の一部:")
                    st.text(text[:500])

            elif file_extension in ['txt', 'csv']: # テキストファイルまたはCSVファイル
                text = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                st.write("ファイル内容の一部:")
                st.text(text[:500])

            # JSON形式で保存          
            value=text
            json_data = {key_value: value}
            st.write(json_data)
            

            # 実行ボタンとキャンセルボタンを表示
            col1, col2 = st.columns(2)
            with col1:
                if st.button("実行"):
                    upload = True

            with col2:
                if st.button("戻る"):
                    cancel = True

    if upload:
        download_path = os.path.expanduser("~/Downloads")
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        # アップロードされたファイル名（拡張子を除去）＋.json
        base_name = os.path.splitext(uploaded_file.name)[0]
        save_file_path = os.path.join(download_path, f"{base_name}.json")

        with open(save_file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        text=""
        st.success(f"ファイルを保存しました: {save_file_path}")
        st.session_state.page = "maintenance"

    # キャンセルボタンが押された場合

    if cancel: 
        #st.rerun()  # ページをリフレッシュ
        
        st.warning("アップロードをキャンセルしました。")
        text=""
        st.session_state.page = "maintenance"

    if st.session_state.uploaded_file is None:
        st.write("ファイルがアップロードされていません。")

    
    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("XMLアップロード"):
        st.session_state.page = "upload_xml"  
    if st.sidebar.button("テキスト入力"):
        st.session_state.page = "input_text" 
    if st.sidebar.button("ファイル削除"):
        st.session_state.page = "delete" 
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"

#テキスト入力のページ
def input_text_page():
    st.title("テキスト入力ページ")
    st.write("現在メンテナンス中です。")

    # セッション状態の初期化
    st.session_state.uploaded_file = None
    upload = False
    cancel = False

    # キー入力用のテキストボックスを追加
    key_value = st.text_input("キーを入力してください")
    st.write(f"入力されたキー: {key_value}")

    # 値入力用のテキストボックスを追加
    value = st.text_input("内容を入力してください")
    st.write(f"入力された内容: {value}")

    # JSON形式で保存            
    json_data = {key_value: value}
    st.write(json_data)

    # 実行ボタンとキャンセルボタンを表示
    col1, col2 = st.columns(2)
    with col1:
        if st.button("実行"):
            upload = True

    with col2:
        if st.button("戻る"):
            cancel = True
    

    if upload:
        download_path = os.path.expanduser("~/Downloads")
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        # アップロードされたファイル名（拡張子を除去）＋.txt
        base_name = key_value.replace(" ", "_")  # スペースをアンダースコアに置換
        save_file_path = os.path.join(download_path, f"{base_name}.json")

        with open(save_file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        st.success(f"ファイルを保存しました: {save_file_path}")
        #st.session_state.uploaded_file = None

    # キャンセルボタンが押された場合

    if cancel: 
        #st.rerun()  # ページをリフレッシュ
        
        st.warning("アップロードをキャンセルしました。")
        st.session_state.page = "maintenance"

    if st.session_state.uploaded_file is None:
        st.write("ファイルがアップロードされていません。")

    
    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("XMLアップロード"):
        st.session_state.page = "upload_xml"  
    if st.sidebar.button("テキストアップロード"):
        st.session_state.page = "upload_text"   
    if st.sidebar.button("ファイル削除"):
        st.session_state.page = "delete" 
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"
       
# 削除ページ
def deleteByPatition_page():
    st.title("削除ページ")
    st.write("現在メンテナンス中です。")

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
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("XMLアップロード"):
        st.session_state.page = "upload_xml" 
    if st.sidebar.button("テキスト入力"):
        st.session_state.page = "input_text"   
    if st.sidebar.button("テキストアップロード"):
        st.session_state.page = "upload_text" 
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
    connection_string = secret_client.get_secret("connectionstringUsers").value
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
    connection_string = secret_client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# Blobデータをアップロード
def upload_blob_data(data):
    connection_string = secret_client.get_secret("connectionstringUsers").value
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
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'login':
    authenticate()
elif st.session_state.page == 'maintenance' and st.session_state.authenticated:
    maintenance_page()
elif st.session_state.page == 'upload_xml':
    upload_xml_page()
elif st.session_state.page == 'input_text':
    input_text_page()
elif st.session_state.page == 'upload_text':
    upload_text_page()
elif st.session_state.page == 'delete':
    deleteByPatition_page()
elif st.session_state.page == 'add_User':
    add_user()
elif st.session_state.page == 'del_User':
    del_user()
elif st.session_state.page == 'admin_login':
    authenticate_admin()
elif st.session_state.page == 'admin':
    admin()


