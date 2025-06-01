import xml.etree.ElementTree as ET
import json

tree = ET.parse('労働基準法.xml')
root = tree.getroot()

# 目次ラベル取得
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
output = {
    "法律名": lawTitle,
    "条文": articles_dict

}

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)