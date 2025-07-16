from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import os
import re
import httpx
import asyncio
from dotenv import load_dotenv
from database import (
    init_database,
    search_lectures,
    get_db_connection,
)
import struct
import math

# ========================
#  環境変数のロード
# ========================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.5-flash:generateContent"
GEMINI_API_URL_FAST = "https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.5-flash:generateContent"

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_API_URL = "https://api.cohere.com/v2/embed"

app = FastAPI()

# データベースを初期化
init_database()

# ------------------------------------------------------------
#  CORS 設定（必要に応じて allow_origins を限定してください）
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ========================
#  Pydantic モデル
# ========================
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


# ========================
#  Gemini API 共通ユーティリティ
# ========================
async def _post_to_gemini(
    payload: Dict[str, Any], max_retries: int = 3, fast: bool = False
) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500, detail="GEMINI_API_KEY が設定されていません"
        )

    url = f"{GEMINI_API_URL_FAST if fast else GEMINI_API_URL}?key={GEMINI_API_KEY}"

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=httpx.Timeout(
                        60.0, connect=10.0
                    ),  # タイムアウトを60秒に延長
                )

            if resp.status_code != 200:
                try:
                    error_data = resp.json()
                    detail = error_data.get("error", {}).get("message", "")

                    # 使用量制限エラーの場合
                    if (
                        resp.status_code == 429
                        or "quota" in detail.lower()
                        or "limit" in detail.lower()
                    ):
                        raise HTTPException(
                            status_code=429,
                            detail="Gemini APIの使用量制限に達しました。しばらく時間をおいてから再試行してください。",
                        )
                except Exception:
                    detail = resp.text[:200]

                raise HTTPException(
                    status_code=500,
                    detail=f"Gemini API Error: {resp.status_code} - {detail}",
                )

            return resp.json()

        except httpx.TimeoutException as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)  # 指数バックオフ
                continue
            else:
                raise HTTPException(
                    status_code=504,
                    detail=f"Gemini API がタイムアウトしました（{max_retries}回試行後）。しばらく時間をおいてから再試行してください。",
                )
        except httpx.RequestError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
                continue
            else:
                raise HTTPException(
                    status_code=503, detail=f"Gemini API への接続エラー: {str(e)}"
                )


def _extract_json(raw: str) -> str:
    """```json ... ``` の三バッククォートやプレーンテキストを除去し、JSON文字列だけを返す"""
    raw = raw.strip()
    # コードフェンス除去
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"```$", "", raw).strip()
    # 先頭の { と最後の } でくくり直す（余分な説明行を避ける）
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start : end + 1]
    return raw


# ========================
#  構造化出力 (JSON) でページを生成
# ========================
async def generate_page_with_ai(prompt: str) -> Dict[str, str]:
    # Gemini への指示を日本語でわかりやすく書く
    system_prompt = f"""
以下の要求に基づいて **JSON 形式のみ** で美しい Web ページを生成してください。マークダウンや追加説明は不要です。

# 要求
{prompt}

# 出力フォーマット (JSON)
{{
  "title": string,             // ページタイトル
  "html_content": string,      // <body> 内 HTML。
  "css_content": string        // ページ全体の CSS。
}}
"""

    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",  # <-- snake_case 仕様
            # schema を指定するとより厳密にできるが、省略しても OK
        },
    }

    result = await _post_to_gemini(payload)

    try:
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=500, detail="Gemini 応答のパースに失敗しました"
        ) from e

    # バッククォートや前置きが混ざっていても取り出せるようにする
    json_text = _extract_json(raw_text)

    try:
        page_json = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"JSON デコード失敗: {e}\nRaw: {json_text[:200]}"
        ) from e

    return {
        "title": page_json.get("title", "AI 生成ページ"),
        "html_content": page_json.get("html_content", ""),
        "css_content": page_json.get("css_content", ""),
    }


# ========================
#  FastAPI ルート
# ========================
@app.get("/")
def root():
    return {"message": "FastAPI is running via Hypercorn!"}


@app.post("/api/generate-page")
async def generate_page(request: PageRequest):
    """フロントエンドからのリクエストを受け取り、Gemini で HTML/CSS を生成して返す"""
    return await generate_page_with_ai(request.prompt)


# ========================
#  講義検索API
# ========================
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
    """講義を検索・フィルタリング"""
    lectures = search_lectures(
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
    return lectures


@app.get("/api/syllabuses/{code}", response_class=HTMLResponse)
def get_syllabus_html(code: str):
    """syllabusesテーブルからcodeが一致するレコードのHTMLを返すAPI"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT html FROM syllabuses WHERE code = ?", (code,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=404, detail="該当するシラバスが見つかりません"
            )
        return row["html"]


# ========================
#  bytes を float のリストに変換する関数
# ========================
def bytes_to_float_list(byte_data: bytes) -> List[float]:
    count = len(byte_data) // 4  # float32 = 4バイト
    return list(struct.unpack(f"{count}f", byte_data))


# ========================
#  Cohere で埋め込み生成（List[float]で返す）
# ========================
async def get_embedding_with_cohere(text: str) -> List[float]:
    if not COHERE_API_KEY:
        raise HTTPException(
            status_code=500, detail="COHERE_API_KEY が設定されていません"
        )

    async def _embed():
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                COHERE_API_URL,
                headers={
                    "Authorization": f"Bearer {COHERE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "embed-multilingual-v3.0",
                    "input_type": "search_query",
                    "texts": [text],
                    "truncate": "END",
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "embeddings" in data:
                    embeddings = data["embeddings"]
                    if "float" in embeddings:
                        return [float(x) for x in embeddings["float"][0]]
                    else:
                        return [float(x) for x in embeddings[0]]
                elif "embeddings_by_type" in data:
                    embeddings_by_type = data["embeddings_by_type"]
                    first_key = list(embeddings_by_type.keys())[0]
                    return [float(x) for x in embeddings_by_type[first_key][0]]
                else:
                    raise Exception(f"予期しないレスポンス構造: {data}")
            else:
                raise Exception(f"Cohere APIエラー: {resp.status_code} - {resp.text}")

    try:
        return await _embed()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cohere埋め込み生成失敗: {str(e)}")


# ========================
#  コサイン類似度計算（NumPyなし版）
# ========================
def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0


# ========================
#  ベクトル検索 (BLOB型vectorカラム)
# ========================
def search_similar_syllabuses(query_vector: List[float], top_k: int = 10):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT code, md, vector FROM syllabuses")
        rows = cursor.fetchall()
    results = []
    for row in rows:
        code, md, vector_bytes = row
        syllabus_vector = bytes_to_float_list(vector_bytes)
        similarity = cosine_similarity(query_vector, syllabus_vector)
        results.append({"code": code, "md": md, "similarity": similarity})
    # 類似度降順でTOP K
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


# ========================
#  RAGエンドポイント
# ========================
class RAGRequest(BaseModel):
    question: str


class RAGResponse(BaseModel):
    answer: str
    references: list


# ========================
#  Gemini QA用（文章のみ返す）
# ========================
async def generate_answer_with_ai(prompt: str, fast: bool = False) -> str:
    system_prompt = f"""
あなたは佐賀大学のマスコット「カッチーくん」です。以下の設定で回答してください：

## キャラクター設定
- 佐賀大学のマスコットキャラクター
- 語尾はタイミングに応じて「カチ」を付ける
- 明るく元気に答える
- 学生や教職員をサポートする熱心なマスコット

## 回答ルール
- 以下のシラバス情報を参考に、ユーザーの質問に答えてください
- 講義内容について答える時は、必ず提供されたシラバス情報のみを参照してください
- 一般知識や推測では絶対に答えないでください
- 情報が不足している場合は、検索結果について言及せず、より具体的な情報を求めてください
- 例：「どんな内容の講義について聞いているカチ？」「どんな分野の講義を探しているカチ？」

# シラバス情報
{prompt}
"""
    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        "generationConfig": {
            "response_mime_type": "text/plain",
        },
    }
    result = await _post_to_gemini(payload, fast=fast)
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=500, detail="Gemini応答のパースに失敗しました"
        ) from e


@app.post("/api/chat")
async def chat(request: RAGRequest):
    query_vector = await get_embedding_with_cohere(request.question)
    results = search_similar_syllabuses(query_vector, top_k=10)
    context = "\n\n".join([row["md"] for row in results])
    prompt = f"""
# シラバス情報
{context}

# ユーザーの質問
{request.question}
"""
    answer = await generate_answer_with_ai(prompt, fast=True)

    def chunker(text):
        import re

        for sentence in re.split(r"(。|！|!|\?|？)", text):
            if sentence.strip():
                yield sentence

    async def event_generator():
        for chunk in chunker(answer):
            yield chunk
            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/plain")


@app.post("/api/chat-sse")
async def chat_sse(request: RAGRequest):
    query_vector = await get_embedding_with_cohere(request.question)
    results = search_similar_syllabuses(query_vector, top_k=10)
    context = "\n\n".join([row["md"] for row in results])
    prompt = f"""
# シラバス情報
{context}

# ユーザーの質問
{request.question}
"""
    answer = await generate_answer_with_ai(prompt, fast=True)

    def chunker(text):
        import re

        for sentence in re.split(r"(。|！|!|\?|？)", text):
            if sentence.strip():
                yield sentence

    async def sse_generator():
        for chunk in chunker(answer):
            # SSE形式でデータを送信
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.05)
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
