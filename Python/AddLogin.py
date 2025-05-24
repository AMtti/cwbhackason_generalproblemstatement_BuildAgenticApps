import streamlit as st

# セッション状態を初期化
if 'page' not in st.session_state:
    st.session_state.page = 'main'

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 認証機能
def authenticate():
    st.title("ログインページ")
    username = st.text_input("IDを入力してください", key="username")
    password = st.text_input("パスワードを入力してください", type="password", key="password")
    if st.button("ログイン"):
        if username == "admin" and password == "password123":  # サンプルのIDとパスワード
            st.session_state.authenticated = True
            st.session_state.page = 'maintenance'
        else:
            st.error("IDまたはパスワードが間違っています！")
    if st.button("メインページに戻る"):
        st.session_state.page = 'main'

# メインページ
def main_page():
    page_bg_color = '''
    <style>
    .stApp {
        background-color: #f0f8ff;
    }
    </style>
    '''
    st.markdown(page_bg_color, unsafe_allow_html=True)
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
    if st.button("メインページに戻る"):
        st.session_state.page = 'main'

# ページ遷移
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'login':
    authenticate()
elif st.session_state.page == 'maintenance' and st.session_state.authenticated:
    maintenance_page()
