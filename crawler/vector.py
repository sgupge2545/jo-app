import csv
import requests
import numpy as np
import os
import time
from typing import Optional


from database import get_db_connection

# Cohere API設定
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_API_URL = "https://api.cohere.com/v2/embed"


def get_embedding(text: str) -> Optional[bytes]:
    """テキストをベクトル化してバイトデータとして返す"""
    try:
        print(f"ベクトル化対象テキスト: {text[:100]}...")  # 最初の100文字を表示

        resp = requests.post(
            COHERE_API_URL,
            headers={
                "Authorization": f"Bearer {COHERE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "embed-multilingual-v3.0",
                "input_type": "search_document",
                "texts": [text],
                "truncate": "END",
            },
            timeout=30,
        )

        print(f"APIレスポンス: {resp.status_code}")

        if resp.status_code == 429:
            print("レート制限に達しました。60秒待機します...")
            time.sleep(60)  # 1分待機
            return None  # 再試行のためにNoneを返す

        if resp.status_code == 200:
            data = resp.json()
            print(f"レスポンスデータ: {data}")

            # レスポンス構造を確認して適切なキーを使用
            if "embeddings" in data:
                embeddings = data["embeddings"]
                if "float" in embeddings:
                    embedding = np.array(embeddings["float"][0], dtype=np.float32)
                else:
                    embedding = np.array(embeddings[0], dtype=np.float32)
            elif "embeddings_by_type" in data:
                # embeddings_by_typeの構造を確認
                embeddings_by_type = data["embeddings_by_type"]
                print(f"embeddings_by_type: {embeddings_by_type}")
                # 最初のキーを取得（通常は"search_document"など）
                first_key = list(embeddings_by_type.keys())[0]
                embedding = np.array(embeddings_by_type[first_key][0], dtype=np.float32)
            else:
                print(f"予期しないレスポンス構造: {data}")
                return None

            return embedding.tobytes()
        else:
            print(f"APIエラー: {resp.status_code} - {resp.text}")
            return None

    except Exception as e:
        print(f"ベクトル化エラー詳細: {e}")
        import traceback

        traceback.print_exc()
        return None


def import_syllabuses_from_csv(
    csv_path: str, batch_size: int = 10, max_rows: int = None
):
    """CSVファイルからシラバスデータをインポート"""
    print(f"CSVファイルを読み込み中: {csv_path}")

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        total_count = 0
        success_count = 0
        error_count = 0

        for row in reader:
            # 最大行数制限
            if max_rows and total_count >= max_rows:
                break
            total_count += 1

            # 進捗表示
            if total_count % 100 == 0:
                print(
                    f"処理中: {total_count}件完了 (成功: {success_count}, エラー: {error_count})"
                )

            try:
                code = row.get("code", "").strip()
                html = row.get("html", "").strip()
                md = row.get("md", "").strip()

                print(
                    f"行 {total_count}: code='{code}', html='{html[:50]}...', md='{md[:50]}...'"
                )

                # 空のデータはスキップ
                if not md:
                    print(f"行 {total_count}: mdが空のためスキップ")
                    continue

                # ベクトル化用のテキストを準備（Markdownのみを使用）
                text_for_embedding = md.strip()

                if not text_for_embedding:
                    print(f"行 {total_count}: text_for_embeddingが空のためスキップ")
                    continue

                # ベクトル化（レート制限エラーの場合は再試行）
                max_retries = 3
                for retry in range(max_retries):
                    vector = get_embedding(text_for_embedding)
                    if vector is not None:
                        break
                    elif retry < max_retries - 1:
                        print(f"行 {total_count}: 再試行 {retry + 1}/{max_retries}")
                        time.sleep(60)  # 1分待機して再試行
                    else:
                        print(f"行 {total_count}: 最大再試行回数に達しました")
                        error_count += 1
                        break

                if vector is None:
                    continue

                # データベースに挿入
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO syllabuses (code, html, md, vector)
                        VALUES (?, ?, ?, ?)
                    """,
                        (code, html, md, vector),
                    )
                    conn.commit()

                success_count += 1

                # バッチサイズごとに進捗を表示
                if success_count % batch_size == 0:
                    print(f"バッチ完了: {success_count}件挿入済み")

            except Exception as e:
                print(f"行 {total_count}: エラー - {e}")
                error_count += 1
                continue

        print(f"\nインポート完了:")
        print(f"総件数: {total_count}")
        print(f"成功: {success_count}")
        print(f"エラー: {error_count}")


def main():
    """メイン関数"""
    csv_path = "./exported_data.csv"

    if not os.path.exists(csv_path):
        print(f"CSVファイルが見つかりません: {csv_path}")
        return

    # データベースを初期化
    from database import init_database

    init_database()

    print("シラバスデータのインポートを開始します...")
    # max_rowsパラメータを削除して全てのデータをインポート
    import_syllabuses_from_csv(csv_path)
    print("インポートが完了しました。")

    # データベースの内容を確認
    print("\n=== データベースの内容確認 ===")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM syllabuses")
        count = cursor.fetchone()[0]
        print(f"syllabusesテーブルの総件数: {count}")

        if count > 0:
            cursor.execute(
                "SELECT id, code, LENGTH(md) as md_length, LENGTH(vector) as vector_length FROM syllabuses LIMIT 3"
            )
            rows = cursor.fetchall()
            print("最初の3件:")
            for row in rows:
                print(
                    f"  ID: {row[0]}, Code: {row[1]}, MD長: {row[2]}, ベクトル長: {row[3]}"
                )


if __name__ == "__main__":
    main()
