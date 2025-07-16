import pandas as pd
from bs4 import BeautifulSoup
import re
import html


def html_to_markdown(html_content):
    """HTMLコンテンツをMarkdownに変換する"""
    if pd.isna(html_content) or html_content == "":
        return ""

    # HTMLエンティティをデコード
    html_content = html.unescape(html_content)

    # BeautifulSoupでパース
    soup = BeautifulSoup(html_content, "html.parser")

    # 不要な要素を削除
    for element in soup.find_all(["script", "style", "button", "form"]):
        element.decompose()

    # テーブルの処理
    for table in soup.find_all("table"):
        markdown_table = convert_table_to_markdown(table)
        table.replace_with(markdown_table)

    # 見出しの処理
    for i in range(1, 7):
        for heading in soup.find_all(f"h{i}"):
            heading_text = heading.get_text(strip=True)
            heading.replace_with(f"\n{'#' * i} {heading_text}\n")

    # 段落の処理
    for p in soup.find_all("p"):
        p_text = p.get_text(strip=True)
        if p_text:
            p.replace_with(f"\n{p_text}\n")

    # リストの処理
    for ul in soup.find_all("ul"):
        markdown_list = convert_list_to_markdown(ul, "ul")
        ul.replace_with(markdown_list)

    for ol in soup.find_all("ol"):
        markdown_list = convert_list_to_markdown(ol, "ol")
        ol.replace_with(markdown_list)

    # リンクの処理
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if href and text:
            a.replace_with(f"[{text}]({href})")

    # 太字と斜体の処理
    for strong in soup.find_all(["strong", "b"]):
        text = strong.get_text(strip=True)
        strong.replace_with(f"**{text}**")

    for em in soup.find_all(["em", "i"]):
        text = em.get_text(strip=True)
        em.replace_with(f"*{text}*")

    # 改行の処理
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # テキストを取得してクリーンアップ
    markdown_text = soup.get_text()

    # 複数の改行を整理
    markdown_text = re.sub(r"\n\s*\n\s*\n", "\n\n", markdown_text)
    markdown_text = re.sub(r" +", " ", markdown_text)

    return markdown_text.strip()


def convert_table_to_markdown(table):
    """テーブルをMarkdown形式に変換"""
    rows = []
    headers = []

    # ヘッダー行を取得
    header_row = table.find("tr")
    if header_row:
        for th in header_row.find_all(["th", "td"]):
            headers.append(th.get_text(strip=True))
        rows.append(headers)

    # データ行を取得
    for tr in table.find_all("tr")[1:]:
        row = []
        for td in tr.find_all("td"):
            row.append(td.get_text(strip=True))
        if row:
            rows.append(row)

    if not rows:
        return ""

    # Markdownテーブルを作成
    markdown_table = []

    # ヘッダー行
    if rows:
        markdown_table.append("| " + " | ".join(rows[0]) + " |")
        markdown_table.append("| " + " | ".join(["---"] * len(rows[0])) + " |")

        # データ行
        for row in rows[1:]:
            markdown_table.append("| " + " | ".join(row) + " |")

    return "\n" + "\n".join(markdown_table) + "\n"


def convert_list_to_markdown(list_element, list_type):
    """リストをMarkdown形式に変換"""
    items = []
    for li in list_element.find_all("li", recursive=False):
        text = li.get_text(strip=True)
        if list_type == "ul":
            items.append(f"* {text}")
        else:
            items.append(f"1. {text}")

    return "\n" + "\n".join(items) + "\n"


def main():
    # CSVファイルを読み込み
    print("CSVファイルを読み込み中...")
    df = pd.read_csv("exported_data.csv")

    print(f"データ数: {len(df)}")
    print("HTMLをMarkdownに変換中...")

    # HTMLをMarkdownに変換
    df["md"] = df["html"].apply(html_to_markdown)

    # 結果を保存
    output_file = "exported_data_with_md.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"変換完了！結果を {output_file} に保存しました。")

    # サンプルを表示
    print("\n=== 変換サンプル ===")
    for i in range(min(3, len(df))):
        print(f"\n--- レコード {i + 1} ---")
        print(f"Code: {df.iloc[i]['code']}")
        print(f"Markdown (最初の200文字): {df.iloc[i]['md'][:200]}...")


if __name__ == "__main__":
    main()
