
import streamlit as st
import asyncio
import pandas as pd

# Add references
from openai import AzureOpenAI
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent,  AzureAIAgentThread

# Azure Cosmos DBのクライアントをインポート
from azure.cosmos import CosmosClient

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential as key_DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# 認証クライアントを作成
key_credential = key_DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=key_credential)

# シークレットの取得
aifoundry_endpoint = secret_client.get_secret("aiFoundryAgentEndpoint").value
model_name=secret_client.get_secret("aiFoundryModel").value

# Cosmos DBの接続情報
client = CosmosClient(
    secret_client.get_secret("cosmosdbendpoint").value,
    secret_client.get_secret("cosmosdbkey").value
    )

#Tread削除関数の定義
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

# Streamlitアプリの設定
st.title("Azure AI Foundry チャットボット")
st.markdown("現在登録されているデータのリストです。相談を入力してください。")
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
                    "content": "[トリアージエージェント] 該当する種別はありません。"
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
                await chat_client.agents.threads.delete(thread.id) if thread else None
            except Exception as e:
                st.warning(f"スレッド削除を実行しました: {e}")
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

