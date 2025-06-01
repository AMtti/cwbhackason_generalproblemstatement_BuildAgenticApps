import asyncio
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent
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

asyncio.run(delete_all_threads())