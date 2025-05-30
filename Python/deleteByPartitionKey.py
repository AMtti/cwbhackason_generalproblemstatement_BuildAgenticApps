from azure.cosmos import CosmosClient
import pandas as pd

import streamlit as st

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Cosmos DBの接続情報
client = CosmosClient(
    secret_client.get_secret("cosmosdbendpoint").value,
    secret_client.get_secret("cosmosdbkey").value
    )


def deleteByPatition_page():
    st.title("データ削除ページ")
    st.write("現在メンテナンス中です。")

    # データベースとコンテナーの情報
    database_name = "LegalNest"
    container_name = "Statute"

    # データベースとコンテナーのクライアント取得
    database = client.get_database_client(database_name)
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

# 階層的に表示するカスタム関数
def display_hierarchical(filtered_df):
    for _, row in filtered_df.iterrows():
        st.write(f"・種別: {row['種別']}")
        st.write(f"　・条文名: {row['条文名']}")
        st.write(f"　　・内容: {row['内容']}\n")

# 階層表示を実行
#display_hierarchical(df)
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

if st.session_state.page == 'delete':
    deleteByPatition_page()

