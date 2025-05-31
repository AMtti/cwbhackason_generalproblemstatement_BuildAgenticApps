import os
import streamlit as st
import asyncio
from pathlib import Path
import pandas as pd

# Add references
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions import kernel_function
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion

from typing import Annotated
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

# Streamlitアプリの設定
st.title("Azure AI Foundry チャットボット")
st.markdown("現在登録されているデータのリストです。相談を入力してください。  \n exit または quit で終了します。")
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
user_message = st.chat_input("あなたのメッセージを入力してください:")

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})

    async def chat_with_agent():
        async with AzureAIAgent.create_client(
            credential=DefaultAzureCredential(),
            endpoint=aifoundry_endpoint
        ) as chat_client:
            # エージェント設定を取得
            agent_settings = await chat_client.agents.create_agent(
                model=model_name,
                name="chat_agent",
                instructions=f"""
                あなたは法律相談のAIアシスタントです。
                以下は現在登録されている種別のリストです: {category_text}
                ユーザーの相談内容に応じて、該当する種別があればそれを優先して回答してください。
                """
            )
            chat_agent = AzureAIAgent(
                client=chat_client,
                definition=agent_settings
            )
            thread = AzureAIAgentThread(client=chat_client, thread_id=st.session_state.thread_id)
            prompt_messages = [f"User: {user_message}"]
            response = await chat_agent.get_response(thread_id=thread.id, messages=prompt_messages)
            
            # 応答を履歴に追加
            st.session_state.messages.append({"role": "assistant", "content": str(response)})
            #await thread.delete() if thread else None
            await chat_client.agents.delete_agent(chat_agent.id)
            # exit/quit でスレッドとエージェントを削除・初期化
            if user_message.strip().lower() in ["exit", "quit"]:
                try:
                    await thread.delete()
                except Exception as e:
                    st.warning(f"スレッド削除を実行しました: {e}")
                try:
                    await st.session_state.chat_client.agents.delete_agent(st.session_state.chat_agent.id)
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



