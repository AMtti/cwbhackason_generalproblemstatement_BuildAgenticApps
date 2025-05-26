import streamlit as st
import pandas as pd #データフレームを扱うためのライブラリ
import os # ファイルアップロードと削除のためのライブラリ
from pypdf import PdfReader # PDFからテキストを抽出するためのライブラリ
import xml.etree.ElementTree as ET # XMLからテキストを抽出するためのライブラリ
import json # JSONファイルを扱うためのライブラリ

from azure.storage.blob import BlobServiceClient # Azure Blob Storageを扱うためのライブラリ

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


    # ファイルアップロードボタンを追加

    col1, col2,col3= st.columns(3)
    with col1:
        if st.button("XMLアップロード"):
            st.session_state.page = "upload_xml"
    with col2:
        if st.button("テキストアップロード"):
            st.session_state.page = "upload_text"
    with col3:
        if st.button("ファイル削除"):
            st.session_state.page = "delete"
   #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"

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
                xml_to_json(root) # XMLをJSONに変換して保存


            
            # 確認ボタンとキャンセルボタンを表示
            col1, col2 = st.columns(2)
            with col1:
                if st.button("確定"):
                    upload = True

            with col2:
                if st.button("キャンセル"):
                    cancel = True

    if upload:
        download_path = os.path.expanduser("~/Downloads")
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        file_path = os.path.join(download_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"ファイルを保存しました: {file_path}")

    if cancel:
        #st.session_state.uploaded_file = None
        #st.rerun()  # ページをリフレッシュ
        st.warning("アップロードをキャンセルしました。")
        st.session_state.page = "maintenance"

    if st.session_state.uploaded_file is None:
        st.write("ファイルがアップロードされていません。")

    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("テキストアップロード"):
        st.session_state.page = "upload_text"   
    if st.sidebar.button("ファイル削除"):
        st.session_state.page = "delete" 
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"

#テキストファイルのアップロードページ
def upload_text_page():
    st.title("テキストファイルアップロードページ")
    st.write("現在メンテナンス中です。")
    # キー入力用のテキストボックスを追加
    key_value = st.text_input("キーを入力してください")
    st.write(f"入力されたキー: {key_value}")

    # セッション状態の初期化
    st.session_state.uploaded_file = None

    # ファイルアップロードボタンを追加
    uploaded_file = st.file_uploader("ファイルをアップロードしてください")
    upload = False
    cancel = False
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        allowed_extensions = ['txt', 'csv', 'pdf']
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1]

        if file_extension not in allowed_extensions:
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

            # XMLファイルはここでは扱わない
            
            # 確認ボタンとキャンセルボタンを表示
            col1, col2 = st.columns(2)
            with col1:
                if st.button("確定"):
                    upload = True

            with col2:
                if st.button("キャンセル"):
                    cancel = True

    if upload:
        download_path = os.path.expanduser("~/Downloads")
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        file_path = os.path.join(download_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"ファイルを保存しました: {file_path}")

    if cancel:
        #st.session_state.uploaded_file = None
        #st.rerun()  # ページをリフレッシュ
        st.warning("アップロードをキャンセルしました。")
        st.session_state.page = "maintenance"

    if st.session_state.uploaded_file is None:
        st.write("ファイルがアップロードされていません。")

    
    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("XMLアップロード"):
        st.session_state.page = "upload_xml"   
    if st.sidebar.button("ファイル削除"):
        st.session_state.page = "delete" 
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"

        
# 削除ページ
def delete_page():
    st.title("削除ページ")
    st.write("現在メンテナンス中です。")

    #サイドバー
    st.sidebar.image("../Ishigame_reading.png", caption="キャプションをここに書く")     
    if st.sidebar.button("XMLアップロード"):
        st.session_state.page = "upload_xml"   
    if st.sidebar.button("テキストアップロード"):
        st.session_state.page = "upload_text" 
    if st.sidebar.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"

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

def xml_to_json(root):

   # tree = ET.parse('労働基準法.xml')
   # root = tree.getroot()

    # 目次ラベル取得
    lawTitle = root.find('.//LawTitle').text

    # すべての条文を処理
    articles_dict = {}
    for article in root.findall('.//Article'):
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

    # JSONデータ作成
    output = {
        "法律名": lawTitle,
        "条文": articles_dict

    }

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


# ページ遷移
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'login':
    authenticate()
elif st.session_state.page == 'maintenance' and st.session_state.authenticated:
    maintenance_page()
elif st.session_state.page == 'upload_xml':
    upload_xml_page()
elif st.session_state.page == 'upload_text':
    upload_text_page()
elif st.session_state.page == 'delete':
    delete_page()


