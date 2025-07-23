#!/home/s23238268/public_html/api/venv/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
import asyncio
import httpx
from urllib.parse import parse_qs, urlencode
import base64
import jwt
from service import (
    get_lectures_service,
    get_syllabus_html_service,
    generate_page_with_ai,
)
from database import (
    get_or_create_user,
    get_timetable_with_lecture_details,
    insert_timetable_entry,
    delete_timetable_entry,
    get_all_users,
    delete_user_timetable,
)
import inspect


def print_json(obj, status=200):
    print("Content-Type: application/json")
    print(f"Status: {status}")
    print()
    print(json.dumps(obj, ensure_ascii=False))


def print_text(text, status=200):
    print("Content-Type: text/plain; charset=utf-8")
    print(f"Status: {status}")
    print()
    print(text)


def print_html(html, status=200):
    print("Content-Type: text/html; charset=utf-8")
    print(f"Status: {status}")
    print()
    print(html)


def get_session_data():
    """セッションデータを取得"""
    cookie = os.environ.get("HTTP_COOKIE", "")
    if not cookie:
        return {}

    # 簡易的なセッション管理（実際の運用ではより安全な方法を使用）
    session_data = {}
    for item in cookie.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            if key == "session_data":
                try:
                    session_data = json.loads(base64.b64decode(value).decode("utf-8"))
                except Exception:
                    pass
    return session_data


def set_session_data(data):
    """セッションデータを設定"""
    session_str = json.dumps(data)
    session_encoded = base64.b64encode(session_str.encode("utf-8")).decode("utf-8")
    print(f"Set-Cookie: session_data={session_encoded}; Path=/; HttpOnly")


def verify_auth():
    """認証を確認"""
    session_data = get_session_data()
    if session_data.get("logged_in") and session_data.get("user_id"):
        return {
            "authenticated": True,
            "user": {
                "id": session_data["user_id"],
                "username": session_data.get("username", ""),
                "email": session_data.get("email", ""),
                "login_time": session_data.get("login_time", 0),
            },
        }
    return {"authenticated": False}


def verify_auth_for_api():
    """API用の認証確認（ユーザー情報のみ返却）"""
    session_data = get_session_data()
    if session_data.get("logged_in") and session_data.get("user_id"):
        return {
            "id": session_data["user_id"],
            "username": session_data.get("username", ""),
            "email": session_data.get("email", ""),
            "login_time": session_data.get("login_time", 0),
        }
    return None


def handle_login():
    """ログイン処理"""
    # Azure Entra ID設定（環境変数から読み込み）
    tenant_id = os.environ.get("MS_TENANT_ID")
    client_id = os.environ.get("MS_CLIENT_ID")
    redirect_uri = os.environ.get("MS_REDIRECT_URI")

    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"

    # リダイレクト先を取得
    query = {}
    if "QUERY_STRING" in os.environ:
        query = {k: v[0] for k, v in parse_qs(os.environ["QUERY_STRING"]).items()}

    redirect = query.get("redirect", "/~s23238268/")

    # セッションにリダイレクト先を保存
    session_data = get_session_data()
    session_data["post_auth_redirect"] = redirect
    set_session_data(session_data)

    # OAuth認証URLを生成
    import secrets

    state = secrets.token_hex(16)
    session_data["oauth_state"] = state
    set_session_data(session_data)

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": f"{redirect_uri}?action=callback",
        "scope": "openid profile email",
        "state": state,
        "response_mode": "query",
    }

    auth_url_with_params = f"{auth_url}?{urlencode(params)}"

    print("Status: 302")
    print(f"Location: {auth_url_with_params}")
    print()


def handle_callback():
    """コールバック処理"""
    # Azure Entra ID設定
    tenant_id = os.environ.get("MS_TENANT_ID")
    client_id = os.environ.get("MS_CLIENT_ID")
    client_secret = os.environ.get("MS_CLIENT_SECRET")
    redirect_uri = os.environ.get("MS_REDIRECT_URI")

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    query = {}
    if "QUERY_STRING" in os.environ:
        query = {k: v[0] for k, v in parse_qs(os.environ["QUERY_STRING"]).items()}

    code = query.get("code", "")
    state = query.get("state", "")

    session_data = get_session_data()

    # ステート検証
    if session_data.get("oauth_state") != state:
        print_json({"error": "Invalid state parameter"}, 400)
        return

    # アクセストークンを取得
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": f"{redirect_uri}?action=callback",
        "scope": "openid profile email",
    }

    try:
        response = httpx.post(token_url, data=token_data, timeout=30.0)
        token_info = response.json()

        # IDトークンからユーザー情報を取得
        if "id_token" not in token_info:
            print_json({"error": f"id_tokenが返されませんでした: {token_info}"}, 400)
            return
        id_token = token_info["id_token"]
        user_info = jwt.decode(id_token, options={"verify_signature": False})

        # ユーザー情報をデータベースに保存
        user = get_or_create_user(
            uid=user_info["sub"],
            name=user_info.get("name", user_info.get("email", "")),
            email=user_info.get("email", ""),
        )

        # セッションに保存
        session_data["user_id"] = user["id"]
        session_data["username"] = user_info.get("name", user_info.get("email", ""))
        session_data["email"] = user_info.get("email", "")
        session_data["logged_in"] = True
        session_data["login_time"] = int(asyncio.get_event_loop().time())
        session_data["access_token"] = token_info["access_token"]

        set_session_data(session_data)

        # 認証後にリダイレクト
        redirect = session_data.get("post_auth_redirect", "/~s23238268/")

        print("Status: 302")
        print(f"Location: {redirect}")
        print()

    except Exception as e:
        print_json({"error": f"Failed to get access token: {str(e)}"}, 400)


def handle_logout():
    """ログアウト処理"""
    tenant_id = os.environ.get("MS_TENANT_ID")

    # セッションを破棄
    print("Set-Cookie: session_data=; Path=/; HttpOnly; Max-Age=0")

    # Azure Entra IDのログアウトURLにリダイレクト
    logout_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout"
    post_logout_redirect_uri = "https://stuext.ai.is.saga-u.ac.jp/~s23238268/"

    logout_params = {"post_logout_redirect_uri": post_logout_redirect_uri}

    full_logout_url = f"{logout_url}?{urlencode(logout_params)}"

    print("Status: 302")
    print(f"Location: {full_logout_url}")
    print()


def check_auth():
    """認証状態を確認"""
    auth_result = verify_auth()
    if auth_result["authenticated"]:
        print_json(auth_result)
    else:
        print_json(auth_result, 401)


def handle_user_login():
    """ユーザーログインAPI"""
    content_length = int(os.environ.get("CONTENT_LENGTH", 0))
    body = sys.stdin.read(content_length)
    data = json.loads(body)

    user = get_or_create_user(
        uid=data["uid"], name=data["name"], email=data.get("email")
    )

    print_json(user)


def handle_get_timetable(user_id):
    """ユーザーの時間割を取得"""
    timetable = get_timetable_with_lecture_details(user_id)
    print_json({"user_id": user_id, "timetable": timetable})


def handle_update_timetable(user_id):
    """時間割を更新"""
    auth_user = verify_auth_for_api()
    if not auth_user:
        print_json({"error": "認証に失敗しました"}, 401)
        return

    if auth_user["id"] != user_id:
        print_json({"error": "自分の時間割のみ更新できます"}, 403)
        return

    content_length = int(os.environ.get("CONTENT_LENGTH", 0))
    body = sys.stdin.read(content_length)
    data = json.loads(body)

    try:
        if data.get("lecture_id") is None:
            # 空き時間にする場合はレコードを削除
            success = delete_timetable_entry(
                user_id, data["day_of_week"], data["period"]
            )
        else:
            # 講義を設定
            insert_timetable_entry(
                user_id, data["day_of_week"], data["period"], data["lecture_id"]
            )
            success = True

        if success:
            print_json({"message": "時間割を更新しました", "success": True})
        else:
            print_json({"message": "時間割の更新に失敗しました", "success": False})
    except Exception as e:
        print_json({"error": f"エラーが発生しました: {str(e)}"}, 500)


def handle_delete_timetable(user_id):
    """ユーザーの時間割を削除"""
    auth_user = verify_auth_for_api()
    if not auth_user:
        print_json({"error": "認証に失敗しました"}, 401)
        return

    if auth_user["id"] != user_id:
        print_json({"error": "自分の時間割のみ削除できます"}, 403)
        return

    success = delete_user_timetable(user_id)
    if success:
        print_json({"message": "時間割を削除しました", "success": True})
    else:
        print_json({"message": "時間割の削除に失敗しました", "success": False})


def handle_get_users():
    """全ユーザーの一覧を取得"""
    users = get_all_users()
    print_json(users)


def handle_get_timetable_by_id(user_id):
    """特定ユーザーの時間割を取得"""
    timetable = get_timetable_with_lecture_details(user_id)
    print_json({"user_id": user_id, "timetable": timetable})


def main():
    path = os.environ.get("PATH_INFO", "")
    method = os.environ.get("REQUEST_METHOD", "GET")
    query = {}
    if "QUERY_STRING" in os.environ:
        query = {k: v[0] for k, v in parse_qs(os.environ["QUERY_STRING"]).items()}

    try:
        if method == "OPTIONS":
            print("Status: 204")
            print("Access-Control-Allow-Origin: *")
            print("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS")
            print("Access-Control-Allow-Headers: Content-Type")
            print()
            return

        # 認証関連のエンドポイント
        if path == "/auth" and method == "GET":
            action = query.get("action", "check")
            if action == "login":
                handle_login()
            elif action == "callback":
                handle_callback()
            elif action == "logout":
                handle_logout()
            elif action == "check":
                check_auth()
            else:
                check_auth()

        # API エンドポイント
        elif path == "/auth/login" and method == "POST":
            handle_user_login()
        elif (
            path.startswith("/users/")
            and path.endswith("/timetable")
            and method == "GET"
        ):
            user_id = int(path.split("/")[-2])
            handle_get_timetable(user_id)
        elif path.startswith("/timetables/") and method == "GET":
            user_id = int(path.split("/")[-1])
            handle_get_timetable_by_id(user_id)
        elif path.startswith("/timetables/") and method == "PUT":
            user_id = int(path.split("/")[-1])
            handle_update_timetable(user_id)
        elif path.startswith("/timetables/") and method == "DELETE":
            user_id = int(path.split("/")[-1])
            handle_delete_timetable(user_id)
        elif path == "/users" and method == "GET":
            handle_get_users()

        # 既存のエンドポイント
        elif path == "/lectures" and method == "GET":
            sig = inspect.signature(get_lectures_service)
            allowed_keys = set(sig.parameters.keys())
            filtered_query = {k: v for k, v in query.items() if k in allowed_keys}
            result = get_lectures_service(**filtered_query)
            print_json(result)
        elif path == "/available-lectures" and method == "GET":
            sig = inspect.signature(get_lectures_service)
            allowed_keys = set(sig.parameters.keys())
            filtered_query = {k: v for k, v in query.items() if k in allowed_keys}
            result = get_lectures_service(**filtered_query)
            print_json(result)
        elif path.startswith("/syllabuses/") and method == "GET":
            code = path.split("/")[-1]
            html = get_syllabus_html_service(code)
            print_html(html)
        elif path == "/generate-page" and method == "POST":
            content_length = int(os.environ.get("CONTENT_LENGTH", 0))
            body = sys.stdin.read(content_length)
            data = json.loads(body)
            result = asyncio.run(generate_page_with_ai(data["prompt"]))
            print_json(result)
        elif path == "/chat" and method == "POST":
            print("Content-Type: text/plain; charset=utf-8\n")
            content_length = int(os.environ.get("CONTENT_LENGTH", 0))
            body = sys.stdin.read(content_length)
            data = json.loads(body)
            from service import chat_service_stream

            async def stream():
                async for chunk in chat_service_stream(data):
                    print(chunk, end="", flush=True)

            asyncio.run(stream())
        else:
            print_json({"error": "Not Found"}, 404)
    except Exception as e:
        print_json({"error": str(e)}, 500)


if __name__ == "__main__":
    main()
