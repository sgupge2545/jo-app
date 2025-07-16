import requests
import numpy as np
from typing import List, Dict, Optional
from database import get_db_connection
import os

# Cohere API設定
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_API_URL = "https://api.cohere.com/v2/embed"


def get_query_embedding(query: str) -> Optional[np.ndarray]:
    """クエリをベクトル化"""
    try:
        resp = requests.post(
            COHERE_API_URL,
            headers={
                "Authorization": f"Bearer {COHERE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "embed-multilingual-v3.0",
                "input_type": "search_query",
                "texts": [query],
                "truncate": "END",
            },
            timeout=30,
        )

        if resp.status_code == 200:
            data = resp.json()

            if "embeddings" in data:
                embeddings = data["embeddings"]
                if "float" in embeddings:
                    return np.array(embeddings["float"][0], dtype=np.float32)
                else:
                    return np.array(embeddings[0], dtype=np.float32)
            elif "embeddings_by_type" in data:
                embeddings_by_type = data["embeddings_by_type"]
                first_key = list(embeddings_by_type.keys())[0]
                return np.array(embeddings_by_type[first_key][0], dtype=np.float32)
            else:
                print(f"予期しないレスポンス構造: {data}")
                return None
        else:
            print(f"APIエラー: {resp.status_code} - {resp.text}")
            return None

    except Exception as e:
        print(f"クエリベクトル化エラー: {e}")
        return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """コサイン類似度を計算"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def search_syllabuses(query: str, top_k: int = 3) -> List[Dict]:
    """シラバスをベクトル検索"""
    print(f"検索クエリ: {query}")

    # クエリをベクトル化
    query_vector = get_query_embedding(query)
    if query_vector is None:
        print("クエリのベクトル化に失敗しました")
        return []

    print(f"クエリベクトル化完了: {len(query_vector)}次元")

    # データベースから全てのシラバスを取得
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, code, md, vector FROM syllabuses")
        rows = cursor.fetchall()

    if not rows:
        print("データベースにシラバスがありません")
        return []

    print(f"データベースから{len(rows)}件のシラバスを取得")

    # 類似度を計算
    results = []
    for row in rows:
        syllabus_id, code, md, vector_bytes = row

        # ベクトルを復元
        syllabus_vector = np.frombuffer(vector_bytes, dtype=np.float32)

        # コサイン類似度を計算
        similarity = cosine_similarity(query_vector, syllabus_vector)

        results.append(
            {"id": syllabus_id, "code": code, "md": md, "similarity": similarity}
        )

    # 類似度でソート（降順）
    results.sort(key=lambda x: x["similarity"], reverse=True)

    # 上位k件を返す
    return results[:top_k]


def demo():
    """デモ実行"""
    print("=== シラバスベクトル検索デモ ===")

    # サンプルクエリ
    sample_queries = [" コンピュータの動作に関する講義は？"]

    for query in sample_queries:
        print(f"\n--- クエリ: '{query}' ---")
        results = search_syllabuses(query, top_k=3)

        if results:
            print(f"検索結果 (上位{len(results)}件):")
            for i, result in enumerate(results, 1):
                print(f"{i}. コード: {result['code']}")
                print(f"   類似度: {result['similarity']:.4f}")
                print(f"   内容: {result['md'][:100]}...")
                print()
        else:
            print("検索結果がありません")

    # インタラクティブ検索
    print("\n=== インタラクティブ検索 ===")
    while True:
        query = input("検索クエリを入力してください (終了: 'quit'): ")
        if query.lower() == "quit":
            break

        if query.strip():
            results = search_syllabuses(query, top_k=3)

            if results:
                print(f"\n検索結果 (上位{len(results)}件):")
                for i, result in enumerate(results, 1):
                    print(f"{i}. コード: {result['code']}")
                    print(f"   類似度: {result['similarity']:.4f}")
                    print(f"   内容: {result['md'][:150]}...")
                    print()
            else:
                print("検索結果がありません")
        else:
            print("クエリを入力してください")


if __name__ == "__main__":
    demo()
