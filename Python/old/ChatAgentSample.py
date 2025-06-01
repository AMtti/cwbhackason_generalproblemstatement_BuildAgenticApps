import os
import streamlit as st
import asyncio
from pathlib import Path

# Add references
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions import kernel_function
from typing import Annotated

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential as key_DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# 認証クライアントを作成
key_credential = key_DefaultAzureCredential()
key_client = SecretClient(vault_url=key_vault_url, credential=key_credential)

# シークレットの取得
aifoundry_endpoint = key_client.get_secret("aiFoundryAgentEndpoint").value
model_name=key_client.get_secret("aiFoundryModel").value

# Streamlitアプリの設定
st.title("Azure AI Foundry チャットボット")
st.markdown("テキストを入力して会話を楽しみましょう！ exit または quit で終了します。")

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
                instructions="You are a helpful assistant for user queries."
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
                    st.warning(f"スレッド削除時にエラーが発生しました: {e}")
                try:
                    await st.session_state.chat_client.agents.delete_agent(st.session_state.chat_agent.id)
                except Exception as e:
                    st.warning(f"エージェント削除時にエラーが発生しました: {e}")
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



