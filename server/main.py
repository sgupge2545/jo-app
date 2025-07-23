import httpx
import base64
import json
from fastapi import FastAPI, Query, HTTPException, Header, Response, Request, Cookie
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
    get_timetable_with_lecture_details,
    insert_timetable_entry,
    delete_timetable_entry,
    get_all_users,
)
import os
import secrets
import jwt
from urllib.parse import urlencode

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


class TimetableAddRequest(BaseModel):
    day_of_week: int  # 1=月, 2=火, 3=水, 4=木, 5=金
    period: int  # 1=1限, 2=2限, ..., 6=6限
    lecture_id: int


class TimetableRemoveRequest(BaseModel):
    day_of_week: int  # 1=月, 2=火, 3=水, 4=木, 5=金
    period: int  # 1=1限, 2=2限, ..., 6=6限


def verify_auth(cookie: str = Header(None)) -> Optional[Dict]:
    """Cookieから直接セッション情報を解析して認証を確認"""
    if not cookie:
        return None

    try:
        # Cookieからセッションデータを抽出
        session_data = {}
        for item in cookie.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                if key == "session_data":
                    try:
                        session_data = json.loads(
                            base64.b64decode(value).decode("utf-8")
                        )
                    except Exception:
                        pass
                    break

        # 認証状態を確認
        if session_data.get("logged_in") and session_data.get("user_id"):
            return {
                "id": session_data["user_id"],
                "username": session_data.get("username", ""),
                "email": session_data.get("email", ""),
                "login_time": session_data.get("login_time", 0),
            }

        return None
    except Exception:
        return None


def set_session_data(response: Response, data: dict):
    session_str = json.dumps(data)
    session_encoded = base64.b64encode(session_str.encode("utf-8")).decode("utf-8")
    response.set_cookie(
        key="session_data", value=session_encoded, path="/", httponly=True
    )


def get_session_data_from_cookie(session_data: Optional[str]) -> dict:
    if not session_data:
        return {}
    try:
        return json.loads(base64.b64decode(session_data).decode("utf-8"))
    except Exception:
        return {}


@app.get("/api/auth")
def auth_action(
    request: Request,
    response: Response,
    action: str = Query("check"),
    session_data: Optional[str] = Cookie(None),
):
    """/auth?action=login|callback|logout|check"""
    # Azure Entra ID設定
    tenant_id = os.environ.get("MS_TENANT_ID", "")
    client_id = os.environ.get("MS_CLIENT_ID", "")
    client_secret = os.environ.get("MS_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("MS_REDIRECT_URI", "")

    session = get_session_data_from_cookie(session_data)

    if action == "login":
        # ログイン処理
        redirect = request.query_params.get("redirect", "/")
        session["post_auth_redirect"] = redirect
        state = secrets.token_hex(16)
        session["oauth_state"] = state
        set_session_data(response, session)
        auth_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        )
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": f"{redirect_uri}?action=callback",
            "scope": "openid profile email",
            "state": state,
            "response_mode": "query",
        }
        auth_url_with_params = f"{auth_url}?{urlencode(params)}"
        response.status_code = 302
        response.headers["Location"] = auth_url_with_params
        return
    elif action == "callback":
        # コールバック処理
        code = request.query_params.get("code", "")
        state = request.query_params.get("state", "")
        if session.get("oauth_state") != state:
            response.status_code = 400
            return {"error": "Invalid state parameter"}
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{redirect_uri}?action=callback",
        }
        try:
            r = httpx.post(token_url, data=token_data, timeout=30.0)
            token_info = r.json()
            id_token = token_info["id_token"]
            user_info = jwt.decode(id_token, options={"verify_signature": False})
            user = get_or_create_user(
                uid=user_info["sub"],
                name=user_info.get("name", user_info.get("email", "")),
                email=user_info.get("email", ""),
            )
            session["user_id"] = user["id"]
            session["username"] = user_info.get("name", user_info.get("email", ""))
            session["email"] = user_info.get("email", "")
            session["logged_in"] = True
            session["login_time"] = int(request.scope.get("time", 0))
            session["access_token"] = token_info["access_token"]
            set_session_data(response, session)
            redirect = session.get("post_auth_redirect", "/")
            response.status_code = 302
            response.headers["Location"] = redirect
            return
        except Exception as e:
            response.status_code = 400
            return {"error": f"Failed to get access token: {str(e)}"}
    elif action == "logout":
        # ログアウト処理
        response.delete_cookie("session_data", path="/")
        logout_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout"
        post_logout_redirect_uri = "https://stuext.ai.is.saga-u.ac.jp/~s23238268/"
        logout_params = {"post_logout_redirect_uri": post_logout_redirect_uri}
        full_logout_url = f"{logout_url}?{urlencode(logout_params)}"
        response.status_code = 302
        response.headers["Location"] = full_logout_url
        return
    elif action == "check":
        # 認証状態確認
        if session.get("logged_in") and session.get("user_id"):
            return {
                "authenticated": True,
                "user": {
                    "id": session["user_id"],
                    "username": session.get("username", ""),
                    "email": session.get("email", ""),
                    "login_time": session.get("login_time", 0),
                },
            }
        else:
            response.status_code = 401
            return {"authenticated": False}
    else:
        response.status_code = 404
        return {"error": "Not Found"}


@app.get("/")
def root():
    return {"message": "FastAPI is running via Hypercorn!"}


@app.post("/api/generate-page")
async def generate_page(
    request: Request, response: Response, session_data: Optional[str] = Cookie(None)
) -> HTMLResponse:
    session = get_session_data_from_cookie(session_data)
    if not session.get("logged_in"):
        raise HTTPException(status_code=401, detail="認証が必要です")
    request.scope["user_id"] = session[
        "user_id"
    ]  # FastAPIのRequestオブジェクトにユーザーIDを設定
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


@app.post("/api/timetables/{user_id}/lectures")
async def add_lecture_to_timetable(
    user_id: int, request: TimetableAddRequest, cookie: str = Header(None)
):
    """時間割に講義を追加（認証付き）"""
    auth_user = verify_auth(cookie)
    if not auth_user:
        raise HTTPException(status_code=401, detail="認証に失敗しました")

    if auth_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="自分の時間割のみ更新できます")

    try:
        insert_timetable_entry(
            user_id, request.day_of_week, request.period, request.lecture_id
        )
        return {"message": "講義を追加しました", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {str(e)}")


@app.post("/api/timetables/{user_id}/lectures/remove")
async def remove_lecture_from_timetable(
    user_id: int, request: TimetableRemoveRequest, cookie: str = Header(None)
):
    """時間割から講義を削除（認証付き）"""
    auth_user = verify_auth(cookie)
    if not auth_user:
        raise HTTPException(status_code=401, detail="認証に失敗しました")

    if auth_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="自分の時間割のみ更新できます")

    try:
        success = delete_timetable_entry(user_id, request.day_of_week, request.period)
        if success:
            return {"message": "講義を削除しました", "success": True}
        else:
            return {"message": "講義の削除に失敗しました", "success": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {str(e)}")


@app.get("/api/users", response_model=List[UserResponse])
def get_users():
    """全ユーザーの一覧を取得"""
    return get_all_users()


@app.get("/api/timetables/{user_id}")
def get_user_timetable_by_id(user_id: int):
    """特定ユーザーの時間割を取得"""
    timetable = get_timetable_with_lecture_details(user_id)
    return {"user_id": user_id, "timetable": timetable}


@app.get("/api/available-lectures", response_model=List[LectureResponse])
def get_available_lectures(
    day: str = Query(..., description="曜日（例: 月, 火, ...）"),
    period: int = Query(..., description="時限（例: 1, 2, ...）"),
):
    from service import get_available_lectures_service

    return get_available_lectures_service(day, period)
