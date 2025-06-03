import streamlit as st
from pages import (
    main_page, authenticate, maintenance_page, upload_xml_page, 
    deleteByPatition_page, add_user, del_user, authenticate_admin, admin, change_password
)

# セッションステートの初期化
if 'page' not in st.session_state:
    st.session_state.page = 'main'

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "current_username" not in st.session_state:
    st.session_state.current_username = None

# ページ遷移
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'login':
    authenticate()
elif st.session_state.page == 'maintenance' and st.session_state.authenticated:
    maintenance_page()
elif st.session_state.page == 'upload_xml':
    upload_xml_page()
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
elif st.session_state.page == "changepassword":
    change_password()

