import requests
from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
from service import (
    generate_page_with_ai,
    get_lectures_service,
    get_syllabus_html_service,
    chat_service,
    init_database_service,
)
from database import (
    get_or_create_user,
    get_user_timetable,
    get_timetable_with_lecture_details,
    insert_timetable_entry,
    delete_timetable_entry,
    get_all_users,
)

app = FastAPI()

# データベースを初期化
init_database_service()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Pydantic モデル
class PageRequest(BaseModel):
    prompt: str


class LectureResponse(BaseModel):
    id: int
    title: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    lecturer: Optional[str] = None
    grade: Optional[str] = None
    class_name: Optional[str] = None
    season: Optional[str] = None
    time: Optional[str] = None


class RAGRequest(BaseModel):
    question: str
    messages: Optional[List[Dict[str, str]]] = []


class RAGResponse(BaseModel):
    answer: str
    references: list


class UserLoginRequest(BaseModel):
    uid: str
    name: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str


class TimetableResponse(BaseModel):
    user_id: int
    timetable: Dict[str, Dict[str, Optional[Dict]]]


class TimetableUpdateRequest(BaseModel):
    day_of_week: int  # 1=月, 2=火, 3=水, 4=木, 5=金
    period: int  # 1=1限, 2=2限, ..., 6=6限
    lecture_id: Optional[int] = None  # nullの場合は空き時間


def verify_php_auth(cookie: str = Header(None)) -> Optional[Dict]:
    """PHPの認証エンドポイントで認証を確認"""
    if not cookie:
        return None

    try:
        # PHPの認証エンドポイントを呼び出し
        response = requests.get(
            "https://stuext.ai.is.saga-u.ac.jp/~s23238268/auth.php?action=check",
            headers={"Cookie": cookie},
            timeout=10,
        )

        if response.status_code == 200:
            auth_data = response.json()
            if auth_data.get("authenticated"):
                return auth_data.get("user")

        return None
    except Exception:
        return None


@app.get("/")
def root():
    return {"message": "FastAPI is running via Hypercorn!"}


@app.post("/api/generate-page")
async def generate_page(request: PageRequest):
    return await generate_page_with_ai(request.prompt)


@app.get("/api/lectures", response_model=List[LectureResponse])
def get_lectures(
    title: Optional[str] = Query(None, description="タイトルでフィルタリング"),
    category: Optional[str] = Query(None, description="カテゴリでフィルタリング"),
    code: Optional[str] = Query(None, description="科目コードでフィルタリング"),
    name: Optional[str] = Query(None, description="科目名でフィルタリング"),
    lecturer: Optional[str] = Query(None, description="担当教員でフィルタリング"),
    grade: Optional[str] = Query(None, description="学年でフィルタリング"),
    class_name: Optional[str] = Query(None, description="クラスでフィルタリング"),
    season: Optional[str] = Query(None, description="開講学期でフィルタリング"),
    time: Optional[str] = Query(None, description="曜日・校時でフィルタリング"),
    keyword: Optional[str] = Query(None, description="全フィールドでキーワード検索"),
):
    return get_lectures_service(
        title=title,
        category=category,
        code=code,
        name=name,
        lecturer=lecturer,
        grade=grade,
        class_name=class_name,
        season=season,
        time=time,
        keyword=keyword,
    )


@app.get("/api/syllabuses/{code}", response_class=HTMLResponse)
def get_syllabus_html(code: str):
    return get_syllabus_html_service(code)


@app.post("/api/chat")
async def chat(request: RAGRequest):
    return await chat_service(request)


@app.post("/api/auth/login", response_model=UserResponse)
def login(request: UserLoginRequest):
    """ユーザーログイン（存在しなければ新規作成）"""
    user = get_or_create_user(uid=request.uid, name=request.name, email=request.email)
    return UserResponse(**user)


@app.get("/api/users/{user_id}/timetable", response_model=TimetableResponse)
def get_user_timetable_api(user_id: int):
    """ユーザーの時間割を取得"""
    timetable = get_timetable_with_lecture_details(user_id)
    return TimetableResponse(user_id=user_id, timetable=timetable)


@app.get("/api/users/{user_id}/timetable/simple")
def get_user_timetable_simple(user_id: int):
    """ユーザーの時間割を取得（講義IDのみ）"""
    timetable = get_user_timetable(user_id)
    return {"user_id": user_id, "timetable": timetable}


@app.put("/api/timetables/{user_id}")
def update_timetable_slot_authenticated(
    user_id: int, request: TimetableUpdateRequest, cookie: str = Header(None)
):
    """特定の時間帯の講義を更新（認証付き）"""
    # PHP認証を確認
    auth_user = verify_php_auth(cookie)
    if not auth_user:
        raise HTTPException(status_code=401, detail="認証に失敗しました")

    # ユーザーIDの一致チェック
    if auth_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="自分の時間割のみ更新できます")

    try:
        if request.lecture_id is None:
            # 空き時間にする場合はレコードを削除
            success = delete_timetable_entry(
                user_id, request.day_of_week, request.period
            )
        else:
            # 講義を設定
            insert_timetable_entry(
                user_id, request.day_of_week, request.period, request.lecture_id
            )
            success = True

        if success:
            return {"message": "時間割を更新しました", "success": True}
        else:
            return {"message": "時間割の更新に失敗しました", "success": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {str(e)}")


@app.delete("/api/timetables/{user_id}")
def delete_user_timetable_authenticated(user_id: int, cookie: str = Header(None)):
    """ユーザーの時間割を全て削除（認証付き）"""
    # PHP認証を確認
    auth_user = verify_php_auth(cookie)
    if not auth_user:
        raise HTTPException(status_code=401, detail="認証に失敗しました")

    # ユーザーIDの一致チェック
    if auth_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="自分の時間割のみ削除できます")

    from database import delete_user_timetable

    success = delete_user_timetable(user_id)
    if success:
        return {"message": "時間割を削除しました", "success": True}
    else:
        return {"message": "時間割の削除に失敗しました", "success": False}


@app.get("/api/users", response_model=List[UserResponse])
def get_users():
    """全ユーザーの一覧を取得"""
    return get_all_users()


@app.get("/api/timetables/{user_id}")
def get_user_timetable_by_id(user_id: int):
    """特定ユーザーの時間割を取得"""
    timetable = get_timetable_with_lecture_details(user_id)
    return {"user_id": user_id, "timetable": timetable}
