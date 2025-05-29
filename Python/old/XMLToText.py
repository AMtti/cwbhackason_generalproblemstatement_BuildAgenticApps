import xml.etree.ElementTree as ET

# XMLファイルを読み込む
tree = ET.parse('労働基準法.xml')
root = tree.getroot()

# XMLからテキストを抽出
def extract_text(element):
    text_content = []
    if element.text:
        text_content.append(element.text.strip())
    for child in element:
        text_content.extend(extract_text(child))
    return text_content

# テキストを収集
text_list = extract_text(root)
print("\n".join(text_list))