from azure.cosmos import CosmosClient # Azure Cosmos DBを扱うためのライブラリ

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

# Azure OpenAIシークレットの取得
aoai_api_key=secret_client.get_secret("textembeddingApiKey").value
aoai_azure_endpoint=secret_client.get_secret("textembeddingEndpoint").value

# Cosmos DBシークレットの取得
cosmosdb_endpoint=secret_client.get_secret("cosmosdbendpoint").value
cosmosdb_key=secret_client.get_secret("cosmosdbkey").value

# Cosmos DB接続情報
cosmosdb_client = CosmosClient(
    cosmosdb_endpoint,
    cosmosdb_key
    )
# Azure Blob Storage の接続情報
connection_string = secret_client.get_secret("connectionstringUsers").value