# ライブラリのインポート
from pypdf import PdfReader


# PDFからテキストを抽出
reader = PdfReader('test2.pdf')
text = ""
for page in reader.pages:
    text += page.extract_text()

# テキストファイルに書き込む
if text == "":
    print("PDFからテキストを抽出できませんでした。PDFが画像のみで構成されている可能性があります。")
else:
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(text)

    print("テキストファイル 'output.txt' に保存しました！")