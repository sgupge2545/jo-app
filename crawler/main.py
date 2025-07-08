import csv
from bs4 import BeautifulSoup


def extract_text_from_p_elements(td_element):
    """td要素内のp要素からテキストを抽出"""
    p_elements = td_element.find_all("p")
    if p_elements:
        return " ".join([p.get_text(strip=True) for p in p_elements])
    else:
        return td_element.get_text(strip=True)


def parse_html_to_csv():
    """HTMLファイルを解析してCSVにエクスポート"""

    # HTMLファイルを読み込み
    with open("data.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(html_content, "html.parser")

    # tbody要素を探す
    tbody = soup.find("tbody")
    if not tbody:
        print("tbody要素が見つかりませんでした")
        return

    # データラベルのマッピング
    data_labels = {
        "タイトル": "title",
        "カテゴリ": "category",
        "科目コード": "code",
        "科目名": "name",
        "担当教員": "lecturer",
        "学年": "grade",
        "クラス": "class",
        "開講学期": "season",
        "曜日・校時": "time",
    }

    # CSVファイルに書き込み
    with open("exported_data.csv", "w", newline="", encoding="utf-8") as csvfile:
        # CSVヘッダーを書き込み
        fieldnames = list(data_labels.values())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # tr要素を順番に処理
        rows = tbody.find_all("tr")
        print(f"処理する行数: {len(rows)}")

        for i, row in enumerate(rows):
            if i % 100 == 0:
                print(f"処理中: {i}/{len(rows)} 行目")

            # 行データを格納する辞書
            row_data = {}

            # 行内のtd要素を処理
            td_elements = row.find_all("td")
            for td in td_elements:
                data_label = td.get("data-label")
                if data_label in data_labels:
                    # p要素からテキストを抽出
                    text = extract_text_from_p_elements(td)
                    row_data[data_labels[data_label]] = text

            # データが存在する場合のみCSVに書き込み
            if row_data:
                writer.writerow(row_data)

    print("CSVエクスポートが完了しました: exported_data.csv")


if __name__ == "__main__":
    parse_html_to_csv()
