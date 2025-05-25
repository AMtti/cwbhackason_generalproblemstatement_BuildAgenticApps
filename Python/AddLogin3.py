import streamlit as st
import os # ファイルアップロードと削除のためのライブラリ
from pypdf import PdfReader # PDFからテキストを抽出するためのライブラリ
import xml.etree.ElementTree as ET # XMLからテキストを抽出するためのライブラリ

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
    username = st.text_input("IDを入力してください", key="username")
    password = st.text_input("パスワードを入力してください", type="password", key="password")
    if st.button("ログイン"):
        if username == "admin" and password == "password123":
            st.session_state.authenticated = True
            st.session_state.page = 'maintenance'
        else:
            st.error("IDまたはパスワードが間違っています！")
    if st.button("メインページに戻る"):
        st.session_state.page = 'main'

# メインページ
def main_page():
    st.title("メインページ")
    st.write("これはメインページです！")

    user_input = st.text_input("お困りごとを教えてください。", value="ここにテキストを入力してください。")
    if user_input:
        st.write(f"あなたが入力した内容: {user_input}")

    if st.button("メンテナンスページへ移動"):
        st.session_state.page = 'login'

# メンテナンスページ
def maintenance_page():
    st.title("メンテナンスページ")
    st.write("現在メンテナンス中です。")


    # ファイルアップロードボタンを追加

    col1, col2 = st.columns(2)
    with col1:
        if st.button("アップロード"):
            st.session_state.page = "upload"

    with col2:
        if st.button("ファイル削除"):
            st.session_state.page = "delete"

    if st.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"

# アップロードページ
def upload_page():
    st.title("アップロードページ")
    st.write("現在メンテナンス中です。")

    # セッション状態の初期化
    st.session_state.uploaded_file = None

    # ファイルアップロードボタンを追加
    uploaded_file = st.file_uploader("ファイルをアップロードしてください")
    upload = False
    cancel = False
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        allowed_extensions = ['txt', 'xml', 'csv', 'pdf']
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1]

        if file_extension not in allowed_extensions:
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
                file_content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                st.write("ファイル内容の一部:")
                st.text(file_content[:500])

            elif file_extension == 'xml': # XMLファイル
                # XMLファイルを読み込む
                tree = ET.parse(uploaded_file)
                root = tree.getroot()
                text_content = extract_text(root)  # ← rootを渡す
                text_str = "\n".join(text_content)  # リストを文字列に変換
                st.write("ファイル内容の一部:")
                st.text(text_str[:500])
            
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

    if st.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.page = "main"


        
# 削除ページ
def delete_page():
    st.title("削除ページ")
    st.write("現在メンテナンス中です。")

    if st.button("メンテナンスページに戻る"):
        st.session_state.page = "maintenance"
    if st.button("ログアウト"):
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
def extract_text(element):
    text_content = []
    if element.text:
        text_content.append(element.text.strip())
    for child in element:
        text_content.extend(extract_text(child))
    return text_content


# ページ遷移
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'login':
    authenticate()
elif st.session_state.page == 'maintenance' and st.session_state.authenticated:
    maintenance_page()
elif st.session_state.page == 'upload':
    upload_page()
elif st.session_state.page == 'delete':
    delete_page()


