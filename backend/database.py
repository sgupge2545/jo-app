import sqlite3
import os
from typing import List, Dict, Optional
from contextlib import contextmanager

# データベースファイルのパス
DB_PATH = "./data/lectures.db"

# データディレクトリを作成
os.makedirs("./data", exist_ok=True)


@contextmanager
def get_db_connection():
    """データベース接続のコンテキストマネージャー"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能にする
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """データベースとテーブルを初期化"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # lecturesテーブルを作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lectures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                category TEXT,
                code TEXT,
                name TEXT,
                lecturer TEXT,
                grade TEXT,
                class TEXT,
                season TEXT,
                time TEXT
            )
        """)

        # 検索用のインデックスを作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON lectures(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON lectures(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_code ON lectures(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON lectures(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lecturer ON lectures(lecturer)")

        conn.commit()
        print("データベースとテーブルが初期化されました")


def insert_lecture(lecture_data: Dict[str, str]) -> int:
    """講義データを挿入"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lectures (title, category, code, name, lecturer, grade, class, season, time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                lecture_data.get("title"),
                lecture_data.get("category"),
                lecture_data.get("code"),
                lecture_data.get("name"),
                lecture_data.get("lecturer"),
                lecture_data.get("grade"),
                lecture_data.get("class"),
                lecture_data.get("season"),
                lecture_data.get("time"),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def search_lectures(
    title: Optional[str] = None,
    category: Optional[str] = None,
    code: Optional[str] = None,
    name: Optional[str] = None,
    lecturer: Optional[str] = None,
    grade: Optional[str] = None,
    class_name: Optional[str] = None,
    season: Optional[str] = None,
    time: Optional[str] = None,
    keyword: Optional[str] = None,
) -> List[Dict]:
    """講義を検索"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # クエリを構築
        query = "SELECT * FROM lectures WHERE 1=1"
        params = []

        # フィルタリング条件
        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")

        if category:
            query += " AND category LIKE ?"
            params.append(f"%{category}%")

        if code:
            query += " AND code LIKE ?"
            params.append(f"%{code}%")

        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")

        if lecturer:
            query += " AND lecturer LIKE ?"
            params.append(f"%{lecturer}%")

        if grade:
            query += " AND grade LIKE ?"
            params.append(f"%{grade}%")

        if class_name:
            query += " AND class LIKE ?"
            params.append(f"%{class_name}%")

        if season:
            query += " AND season LIKE ?"
            params.append(f"%{season}%")

        if time:
            query += " AND time LIKE ?"
            params.append(f"%{time}%")

        # キーワード検索（全フィールドを対象）
        if keyword:
            query += """ AND (
                title LIKE ? OR 
                category LIKE ? OR 
                code LIKE ? OR 
                name LIKE ? OR 
                lecturer LIKE ? OR 
                grade LIKE ? OR 
                class LIKE ? OR 
                season LIKE ? OR 
                time LIKE ?
            )"""
            keyword_param = f"%{keyword}%"
            params.extend([keyword_param] * 9)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 辞書のリストに変換
        return [dict(row) for row in rows]
