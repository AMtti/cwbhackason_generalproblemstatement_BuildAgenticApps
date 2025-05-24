import streamlit as st

# ページ遷移用のセッション状態を初期化
if 'page' not in st.session_state:
    st.session_state.page = 'main'  # 最初はメインページからスタート

# ページごとの関数
def main_page():
    # CSSで背景画像を設定
    page_bg_color = '''
    <style>
    .stApp {
        background-color: #f0f8ff; /* ここで色を指定します。例: #f0f8ff (薄い青) */
    }
    </style>
    '''

    st.markdown(page_bg_color, unsafe_allow_html=True)
    st.title("メインページ")
    st.write("これはメインページです！")

    # テキスト入力欄を作成
    user_input = st.text_input("お困りごとを教えてください。", value="ここにテキストを入力してください。")

    # 入力内容を表示
    if user_input:
        st.write(f"あなたが入力した内容: {user_input}")
    # メンテナンスページへのボタン
    if st.button("メンテナンスページへ移動"):
        st.session_state.page = 'maintenance'

def maintenance_page():
    st.title("メンテナンスページ")
    st.write("現在メンテナンス中です。")
    # メインページへのボタン
    if st.button("メインページに戻る"):
        st.session_state.page = 'main'

# 現在のページに応じた処理を実行
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'maintenance':
    maintenance_page()
