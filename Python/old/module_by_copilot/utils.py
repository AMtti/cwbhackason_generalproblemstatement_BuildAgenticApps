import json
import uuid

from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient, PartitionKey
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from pypdf import PdfReader

#keyVaultの情報を取得
key_vault_url = "https://keytaccountcwbhackasonam.vault.azure.net/"
key_credential = DefaultAzureCredential()
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
def get_credentials_from_blob(secret_client):
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

#管理者の認証情報を取得
def get_admin_credentials_from_blob(secret_client):
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

# Blobデータをダウンロード
def download_blob_data(secret_client):
    connection_string = secret_client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)

# Blobデータをアップロード
def upload_blob_data(secret_client, data):
    connection_string = secret_client.get_secret("connectionstringUsers").value
    container_name = "users"
    blob_name = "users.json"

    # Blob Storage に接続
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(json.dumps(data), overwrite=True)

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


# 埋め込み作成してAzure Cosmos DBに保存する関数
def create_embedding_and_save_to_cosmos_db(secret_client, json_data):
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