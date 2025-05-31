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
st.markdown("テキストを入力して会話を楽しみましょう！")

# 会話スレッドを初期化
if "thread_id" not in st.session_state:
    async def initialize_thread():
        async with (
        DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True) as creds,
            AzureAIAgent.create_client(
            credential=creds,
            endpoint=aifoundry_endpoint
        )as client,
    ):
            thread = await client.agents.threads.create()
            st.session_state.thread_id = thread.id
    asyncio.run(initialize_thread())

# ユーザー入力
user_message = st.text_input("あなたのメッセージを入力してください:")

# メッセージ送信と応答取得
if st.button("送信") and user_message:
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
            chat_agent =AzureAIAgent(
                client=chat_client,
                definition=agent_settings
            )
            
            
            # メッセージ送信
            thread = AzureAIAgentThread(client=chat_client, thread_id=st.session_state.thread_id)
            prompt_messages = [f"User: {user_message}"]
            response = await chat_agent.get_response(thread_id=thread.id, messages=prompt_messages)
                        
            # 応答を表示
            st.write(f"🤖 エージェント: {response}")
            

            # Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await chat_client.agents.delete_agent(chat_agent.id)


    asyncio.run(chat_with_agent())
    



