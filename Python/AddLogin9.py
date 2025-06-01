import streamlit as st # Streamlitを使用してWebアプリケーションを作成するためのライブラリ
import asyncio # 非同期処理を扱うためのライブラリ
import pandas as pd #データフレームを扱うためのライブラリ
from pypdf import PdfReader # PDFからテキストを抽出するためのライブラリ
import xml.etree.ElementTree as ET # XMLからテキストを抽出するためのライブラリ
import json # JSONファイルを扱うためのライブラリ

from azure.storage.blob import BlobServiceClient # Azure Blob Storageを扱うためのライブラリ

from azure.cosmos import CosmosClient, PartitionKey # Azure Cosmos DBを扱うためのライブラリ
from openai import AzureOpenAI  # OpenAIのAPIを扱うためのライブラリ
from azure.identity.aio import DefaultAzureCredential # Azureの認証を扱うためのライブラリ
from semantic_kernel.agents import AzureAIAgent,  AzureAIAgentThread  # Azure AI Foundryのエージェントを扱うためのライブラリ  
import uuid # UUIDを生成するためのライブラリ

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential as key_DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"
# Azure へのログインが必要な場合の例外処理
from azure.core.exceptions import ClientAuthenticationError

try:
    key_credential = key_DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=key_credential)
    # シークレットの取得例
    aifoundry_endpoint = secret_client.get_secret("aiFoundryAgentEndpoint").value
except ClientAuthenticationError:
    st.error("Azure にログインしてから再度実行してください。")
    st.stop()
except Exception as e:
    st.error(f"Azure認証エラー: {e}")
    st.stop()

# Key Vault 認証クライアントを作成
key_credential = key_DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=key_credential)

# AI Foundryシークレットの取得
aifoundry_endpoint = secret_client.get_secret("aiFoundryAgentEndpoint").value
model_name=secret_client.get_secret("aiFoundryModel").value

# Cosmos DBの接続情報
cosmosdb_client = CosmosClient(
    secret_client.get_secret("cosmosdbendpoint").value,
    secret_client.get_secret("cosmosdbkey").value
    )


 # Azure Blob Storage の接続情報
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

if "current_username" not in st.session_state:
    st.session_state.current_username = None

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

# メインページ
#AI Foundry Agent Thread削除関数の定義
async def delete_all_threads():
    async with AzureAIAgent.create_client(
        credential=DefaultAzureCredential(),
        endpoint=aifoundry_endpoint
    ) as chat_client:
        # まず全スレッドIDをリストとして取得
        threads = chat_client.agents.threads.list()
        thread_ids = []
        async for thread in threads:
            thread_ids.append(thread.id)

        count = 0
        for thread_id in thread_ids:
            try:
                await chat_client.agents.threads.delete(thread_id)
                print(f"Deleted thread: {thread_id}")
                count += 1
            except Exception as e:
                print(f"Failed to delete thread {thread_id}: {e}")
        print(f"Total deleted: {count}")

def main_page():
    # Streamlitアプリの設定
    st.title("困りごと相談AIアプリ")
    st.markdown("現在登録されているデータのリストです。相談を入力してください。")

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
        category_list = df['種別'].unique().tolist()
        category_text = "、".join(category_list)

    # Azure OpenAI クライアントの設定
    textembedding_client = AzureOpenAI(
        api_key=secret_client.get_secret("textembeddingApiKey").value,
        api_version="2024-12-01-preview",
        azure_endpoint=secret_client.get_secret("textembeddingEndpoint").value
    )

    # 会話スレッドを初期化
    if "thread_id" not in st.session_state:
        async def initialize_thread():
            async with AzureAIAgent.create_client(
                credential=DefaultAzureCredential(),
                endpoint=aifoundry_endpoint
            ) as chat_client:
                thread = await chat_client.agents.threads.create()
                return thread.id
        st.session_state.thread_id = asyncio.run(initialize_thread())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # チャットUI
    user_message = st.chat_input("あなたのメッセージを入力してください(exit または quit で終了します。):")

    if user_message:
        st.session_state.messages.append({"role": "user", "content": user_message})

        async def chat_with_agent():
            async with AzureAIAgent.create_client(
                credential=DefaultAzureCredential(),
                endpoint=aifoundry_endpoint
            ) as chat_client:
                # 1. トリアージエージェント
                triage_settings = await chat_client.agents.create_agent(
                    model=model_name,
                    name="triage_agent",
                    instructions=f"""
                    あなたはユーザーの相談内容から、以下の種別リストに該当するものがあるか判定するAIです。
                    種別リスト: {category_text}
                    ユーザーの入力に該当する種別があれば、その種別名だけを返してください。なければ「なし」とだけ返してください。
                    """
                )
                triage_agent = AzureAIAgent(
                    client=chat_client,
                    definition=triage_settings
                )

                # 2. 法律検索エージェント
                law_search_settings = await chat_client.agents.create_agent(
                    model=model_name,
                    name="law_search_agent",
                    instructions=f"""
                    あなたは法律検索の専門AIです。ユーザーの相談内容と該当種別に基づき、関連する法律情報を詳しく調べて回答してください。
                    種別リスト: {category_text}
                    """
                )
                law_search_agent = AzureAIAgent(
                    client=chat_client,
                    definition=law_search_settings
                )

                # 3. アシスタントエージェント
                chat_settings = await chat_client.agents.create_agent(
                    model=model_name,
                    name="assistant_agent",
                    instructions="あなたは法律相談のAIアシスタントです。一般的な質問に親切に答えてください。"
                )
                assistant_agent = AzureAIAgent(
                    client=chat_client,
                    definition=chat_settings
                )

                thread = AzureAIAgentThread(client=chat_client, thread_id=st.session_state.thread_id)

                # --- トリアージ判定 ---
                triage_prompt = [f"User: {user_message}"]
                triage_result = await triage_agent.get_response(thread_id=thread.id, messages=triage_prompt)
                triage_result_text = str(triage_result).strip()
                # トリアージ結果を履歴に追加
                if triage_result_text != "なし":
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"[トリアージエージェント] 判定結果: {triage_result_text}のデータを検索します。"
                    })
                else:    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "[トリアージエージェント] 該当するデータはありません。"
                    })
                    
                # --- 振り分け ---
                if triage_result_text != "なし":
                    # ここでベクトル検索を実行し、結果をプロンプトに含める
                    # 類似検索に使用するベクトル埋め込みデータ
                    response = textembedding_client.embeddings.create(
                        input=user_message,
                        model="text-embedding-3-large"
                    )
                    query_embedding = response.data[0].embedding

                    # Query for items 
                    search_results = []
                    for item in container.query_items(
                        query="""
                            SELECT TOP 3 c.条文名, c.内容, VectorDistance(c.embedding, @embedding) AS SimilarityScore
                            FROM c
                            WHERE c.種別 = @type
                            ORDER BY VectorDistance(c.embedding, @embedding)
                        """,
                        parameters=[
                            {"name": "@embedding", "value": query_embedding},
                            {"name": "@type", "value": triage_result_text}
                        ],
                        enable_cross_partition_query=True
                    ):
                        search_results.append(item)

                    # 検索結果をテキスト化
                    if search_results:
                        law_info = f"【参考条文】\n①条文名: {search_results[0]['条文名']}\n内容: {search_results[0]['内容']}\n②条文名: {search_results[1]['条文名']}\n内容: {search_results[1]['内容']}\n③条文名: {search_results[2]['条文名']}\n内容: {search_results[2]['内容']}"
                        
                        def score_to_percent(score):
                            # 距離が0に近いほど類似度が高いので、(1 - 距離) * 100 でパーセント化（0～1の範囲を想定）
                            percent = max(0, min(100, round((1 - float(score)) * 100)))
                            return percent

                        statute_name = (
                            f"【参考条文】  \n"
                            f"①条文名: {search_results[0]['条文名']}（類似度: {score_to_percent(search_results[0]['SimilarityScore'])}%）  \n"
                            f"②条文名: {search_results[1]['条文名']}（類似度: {score_to_percent(search_results[1]['SimilarityScore'])}%）  \n"
                            f"③条文名: {search_results[2]['条文名']}（類似度: {score_to_percent(search_results[2]['SimilarityScore'])}%）"
                        )
                    else:
                        law_info = "該当する条文は見つかりませんでした。"

                    # 法律検索エージェントへのプロンプトに追加
                    prompt_messages = [
                        f"User: {user_message}",
                        law_info  # ここで追加
                    ]
                    response = await law_search_agent.get_response(thread_id=thread.id, messages=prompt_messages)
                    agent_name = "法律検索エージェント"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content":f"[{agent_name}] {str(statute_name)}"
                    })
                else:
                    # 該当する種別がない場合 → assistant_agent
                    response = await assistant_agent.get_response(thread_id=thread.id, messages=[f"User: {user_message}"])
                    agent_name = "アシスタントエージェント"
            
                # 応答を履歴に追加
                st.session_state.messages.append({"role": "assistant", "content": f"[{agent_name}] {str(response)}"})

                try:
                    await chat_client.agents.delete_agent(triage_agent.id)
                except Exception as e:
                    st.warning(f"トリアージエージェント削除を実行しました: {e}")
                try:
                    await chat_client.agents.delete_agent(law_search_agent.id)
                except Exception as e:
                    st.warning(f"法律検索エージェント削除を実行しました: {e}")
                try:
                    await chat_client.agents.delete_agent(assistant_agent.id)
                except Exception as e:
                    st.warning(f"アシスタントエージェント削除を実行しました: {e}")
                # exit/quit でスレッドとエージェントを削除・初期化
                if user_message.strip().lower() in ["exit", "quit"]:
                    try:
                        await delete_all_threads()
                    except Exception as e:
                        st.warning(f"スレッド削除を実行しました: {e}")
                    try:
                        await st.session_state.chat_client.agents.delete_agent(st.session_state.triage_agent.id)
                    except Exception as e:
                        st.warning(f"エージェント削除を実行しました: {e}")                   
                    try:
                        await st.session_state.chat_client.agents.delete_agent(st.session_state.law_search_agent.id)
                    except Exception as e:
                        st.warning(f"エージェント削除を実行しました: {e}")
                    try:
                        await st.session_state.chat_client.agents.delete_agent(st.session_state.assistant_agent.id)
                    except Exception as e:
                        st.warning(f"エージェント削除を実行しました: {e}")
                    # セッション状態を初期化
                    st.session_state.clear()
                    st.rerun()
                    


        asyncio.run(chat_with_agent())




    # 会話履歴の表示
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])
   
    #サイドバー
    st.sidebar.image("../PNG/Ishigame_reading.png", caption="")     
    if st.sidebar.button("メンテナンスページへ移動"):
        st.session_state.page = 'login'

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

