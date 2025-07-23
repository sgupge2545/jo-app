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

        # usersテーブルを作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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
                class_name TEXT,
                season TEXT,
                time TEXT
            )
        """)

        # syllabusesテーブルを作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS syllabuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                html TEXT,
                md TEXT,
                vector BLOB
            )
        """)

        # lecture_timetablesテーブルを作成（中間テーブル方式）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lecture_timetables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                period INTEGER NOT NULL,
                lecture_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (lecture_id) REFERENCES lectures(id),
                UNIQUE(user_id, day_of_week, period)
            )
        """)

        # 検索用のインデックスを作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_uid ON users(uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON lectures(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON lectures(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_code ON lectures(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON lectures(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lecturer ON lectures(lecturer)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timetable_user ON lecture_timetables(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timetable_day_period ON lecture_timetables(day_of_week, period)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timetable_lecture ON lecture_timetables(lecture_id)"
        )

        conn.commit()
        print("データベースとテーブルが初期化されました")


def migrate_syllabuses_table():
    """syllabusesテーブルにcodeカラムを追加するマイグレーション"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # テーブルの構造を確認
        cursor.execute("PRAGMA table_info(syllabuses)")
        columns = [column[1] for column in cursor.fetchall()]

        # codeカラムが存在しない場合は追加
        if "code" not in columns:
            cursor.execute("ALTER TABLE syllabuses ADD COLUMN code TEXT")
            conn.commit()
            print("syllabusesテーブルにcodeカラムを追加しました")
        else:
            print("codeカラムは既に存在します")


def insert_lecture(lecture_data: Dict[str, str]) -> int:
    """講義データを挿入"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lectures (title, category, code, name, lecturer, grade, class_name, season, time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                lecture_data.get("title"),
                lecture_data.get("category"),
                lecture_data.get("code"),
                lecture_data.get("name"),
                lecture_data.get("lecturer"),
                lecture_data.get("grade"),
                lecture_data.get("class_name"),
                lecture_data.get("season"),
                lecture_data.get("time"),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def insert_syllabus(code: str, html: str, md: str, vector: bytes) -> int:
    """シラバスデータを挿入"""
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
        return cursor.lastrowid


def get_syllabus(syllabus_id: int) -> Optional[Dict]:
    """シラバスデータを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM syllabuses WHERE id = ?", (syllabus_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_syllabuses() -> List[Dict]:
    """全てのシラバスデータを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM syllabuses")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


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
            query += " AND class_name LIKE ?"
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
                class_name LIKE ? OR 
                season LIKE ? OR 
                time LIKE ?
            )"""
            keyword_param = f"%{keyword}%"
            params.extend([keyword_param] * 9)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 辞書のリストに変換
        return [dict(row) for row in rows]


def create_empty_timetable() -> dict:
    """空の時間割テンプレートを作成"""
    timetable = {}
    for day in range(1, 6):  # 月曜(1)から金曜(5)
        timetable[str(day)] = {}
        for period in range(1, 7):  # 1限から6限
            timetable[str(day)][str(period)] = None
    return timetable


# Users テーブル用の関数
def create_user(uid: str, name: str, email: Optional[str] = None) -> int:
    """ユーザーを作成"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (uid, name, email)
            VALUES (?, ?, ?)
            """,
            (uid, name, email),
        )
        conn.commit()
        return cursor.lastrowid


def get_user_by_uid(uid: str) -> Optional[Dict]:
    """UIDでユーザーを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """IDでユーザーを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user(
    user_id: int, name: Optional[str] = None, email: Optional[str] = None
) -> bool:
    """ユーザー情報を更新"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 更新するフィールドを動的に構築
        update_fields = []
        params = []

        if name is not None:
            update_fields.append("name = ?")
            params.append(name)

        if email is not None:
            update_fields.append("email = ?")
            params.append(email)

        if not update_fields:
            return False

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    """ユーザーを削除（関連する時間割も削除）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 関連する時間割を先に削除
        cursor.execute("DELETE FROM lecture_timetables WHERE user_id = ?", (user_id,))

        # ユーザーを削除
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_or_create_user(uid: str, name: str, email: Optional[str] = None) -> Dict:
    """ユーザーを取得、存在しなければ作成"""
    user = get_user_by_uid(uid)
    if user:
        return user

    user_id = create_user(uid, name, email)
    return get_user_by_id(user_id)


def get_all_users() -> List[Dict]:
    """全ユーザーの一覧を取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name
            FROM users
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# 時間割関連の関数（中間テーブル方式）
def insert_timetable_entry(
    user_id: int, day_of_week: int, period: int, lecture_id: Optional[int] = None
) -> int:
    """時間割エントリを挿入または更新"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 既存のエントリがあるかチェック
        cursor.execute(
            "SELECT id FROM lecture_timetables WHERE user_id = ? AND day_of_week = ? AND period = ?",
            (user_id, day_of_week, period),
        )
        existing = cursor.fetchone()

        if existing:
            # 既存のエントリを更新
            cursor.execute(
                """
                UPDATE lecture_timetables 
                SET lecture_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND day_of_week = ? AND period = ?
                """,
                (lecture_id, user_id, day_of_week, period),
            )
            conn.commit()
            return existing[0]
        else:
            # 新しいエントリを挿入
            cursor.execute(
                """
                INSERT INTO lecture_timetables (user_id, day_of_week, period, lecture_id)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, day_of_week, period, lecture_id),
            )
            conn.commit()
            return cursor.lastrowid


def get_user_timetable(user_id: int) -> dict:
    """ユーザーの時間割を取得（辞書形式で返す）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT day_of_week, period, lecture_id
            FROM lecture_timetables 
            WHERE user_id = ?
            ORDER BY day_of_week, period
        """,
            (user_id,),
        )
        rows = cursor.fetchall()

        # 辞書形式に変換
        timetable = create_empty_timetable()
        for row in rows:
            day = str(row[0])
            period = str(row[1])
            lecture_id = row[2]
            timetable[day][period] = lecture_id

        return timetable


def get_timetable_with_lecture_details(user_id: int) -> dict:
    """講義詳細情報付きで時間割を取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                tt.day_of_week,
                tt.period,
                tt.lecture_id,
                l.title,
                l.name,
                l.lecturer,
                l.time,
                l.category,
                l.code
            FROM lecture_timetables tt
            LEFT JOIN lectures l ON tt.lecture_id = l.id
            WHERE tt.user_id = ?
            ORDER BY tt.day_of_week, tt.period
        """,
            (user_id,),
        )
        rows = cursor.fetchall()

        # 辞書形式に変換
        detailed_timetable = create_empty_timetable()
        for row in rows:
            day = str(row[0])
            period = str(row[1])
            lecture_id = row[2]

            if lecture_id:
                # 講義詳細情報を辞書に変換
                lecture_data = {
                    "id": lecture_id,
                    "title": row[3],
                    "name": row[4],
                    "lecturer": row[5],
                    "time": row[6],
                    "category": row[7],
                    "code": row[8],
                }
                detailed_timetable[day][period] = lecture_data
            else:
                detailed_timetable[day][period] = None

        return detailed_timetable


def update_timetable_slot(
    user_id: int, day_of_week: int, period: int, lecture_id: Optional[int]
) -> bool:
    """特定の時間帯の講義を更新"""
    try:
        insert_timetable_entry(user_id, day_of_week, period, lecture_id)
        return True
    except Exception:
        return False


def delete_timetable_entry(user_id: int, day_of_week: int, period: int) -> bool:
    """時間割エントリを削除"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM lecture_timetables WHERE user_id = ? AND day_of_week = ? AND period = ?",
            (user_id, day_of_week, period),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_user_timetable(user_id: int) -> bool:
    """ユーザーの時間割を削除"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lecture_timetables WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_users_by_lecture(lecture_id: int) -> List[Dict]:
    """特定の講義を取っているユーザーを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                u.id,
                u.uid,
                u.name,
                u.email,
                tt.day_of_week,
                tt.period
            FROM lecture_timetables tt
            JOIN users u ON tt.user_id = u.id
            WHERE tt.lecture_id = ?
            ORDER BY u.name, tt.day_of_week, tt.period
        """,
            (lecture_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
