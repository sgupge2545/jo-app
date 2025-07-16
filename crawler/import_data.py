import csv
import sys
import os
from database import init_database, insert_lecture


def import_from_csv(csv_file_path: str):
    """CSVファイルからデータをインポート"""

    # データベースを初期化
    init_database()

    # CSVファイルを読み込み
    with open(csv_file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        count = 0
        for row in reader:
            # CSVのカラム名をデータベースのカラム名にマッピング
            lecture_data = {
                "title": row.get("title", ""),
                "category": row.get("category", ""),
                "code": row.get("code", ""),
                "name": row.get("name", ""),
                "lecturer": row.get("lecturer", ""),
                "grade": row.get("grade", ""),
                "class": row.get("class", ""),
                "season": row.get("season", ""),
                "time": row.get("time", ""),
            }

            # データベースに挿入
            insert_lecture(lecture_data)
            count += 1

            if count % 100 == 0:
                print(f"処理済み: {count}件")

    print(f"完了: {count}件のデータをインポートしました")


if __name__ == "__main__":
    # CSVファイルのパスを指定（デフォルトはcrawler/exported_data.csv）
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "../crawler/exported_data.csv"

    if not os.path.exists(csv_path):
        print(f"エラー: CSVファイルが見つかりません: {csv_path}")
        sys.exit(1)

    print(f"CSVファイルをインポート中: {csv_path}")
    import_from_csv(csv_path)
