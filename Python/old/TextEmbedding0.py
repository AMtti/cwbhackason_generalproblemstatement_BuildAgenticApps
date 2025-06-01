from openai import AzureOpenAI
#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)

# Azure OpenAI クライアントの設定
client = AzureOpenAI(
    api_key=client.get_secret("textembeddingApiKey").value,
    api_version="2024-12-01-preview",
    azure_endpoint=client.get_secret("textembeddingEndpoint").value
)

response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-large"
)

print(response.model_dump_json(indent=2))