# Azure Key Vaultからシークレットを取得するためのコード

#keyVaultの情報を取得
from azure.identity import DefaultAzureCredential as key_DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URI
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"

# Key Vault 認証クライアントを作成
key_credential = key_DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=key_credential)

# AI Foundryシークレットの取得
aifoundry_endpoint = secret_client.get_secret("aiFoundryAgentEndpoint").value
aifoundry_chatmodel = "gpt-4o"

# Azure OpenAIシークレットの取得
aoai_api_key=secret_client.get_secret("textembeddingApiKey").value
aoai_azure_endpoint=secret_client.get_secret("textembeddingEndpoint").value
aoai_embedingmodel="text-embedding-3-large"
# Cosmos DBシークレットの取得
cosmosdb_endpoint=secret_client.get_secret("cosmosdbendpoint").value
cosmosdb_key=secret_client.get_secret("cosmosdbkey").value
# データベースとコンテナーの情報
database_name = "LegalNest"
container_name = "Statute"

# Azure Blob Storage シークレットの取得
connection_string = secret_client.get_secret("connectionstringUsers").value