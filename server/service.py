import json
import os
import re
import httpx
import asyncio
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
from dotenv import load_dotenv
from database import (
    search_lectures,
    get_db_connection,
)


# ========================
#  環境変数のロード
# ========================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.5-flash:generateContent"
GEMINI_API_URL_FAST = "https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.5-flash:generateContent"

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_API_URL = "https://api.cohere.com/v2/embed"


# ========================
#  データベース初期化
# ========================
def init_database_service():
    from database import init_database

    init_database()


# ========================
#  講義情報取得関数（code指定）
# ========================
def get_lecture_by_code(code: str):
    """codeに基づいて講義情報を取得（複数の場合は最初の一件）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, lecturer, grade, class_name, time FROM lectures WHERE code = ? LIMIT 1",
            (code,),
        )
        row = cursor.fetchone()
        return row


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
                    timeout=httpx.Timeout(60.0, connect=10.0),
                )

            if resp.status_code != 200:
                try:
                    error_data = resp.json()
                    detail = error_data.get("error", {}).get("message", "")
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
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
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
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start : end + 1]
    return raw


# ========================
#  構造化出力 (JSON) でページを生成
# ========================
async def generate_page_with_ai(prompt: str) -> Dict[str, str]:
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
            "response_mime_type": "application/json",
        },
    }
    result = await _post_to_gemini(payload)
    try:
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=500, detail="Gemini 応答のパースに失敗しました"
        ) from e
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
#  講義検索API
# ========================
def get_lectures_service(
    title=None,
    category=None,
    code=None,
    name=None,
    lecturer=None,
    grade=None,
    class_name=None,
    season=None,
    time=None,
    keyword=None,
):
    return search_lectures(
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


# ========================
#  シラバスHTML取得API
# ========================
def get_syllabus_html_service(code: str):
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
#  Cohere で埋め込み生成
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
#  Gemini QA用（文章のみ返す）
# ========================
async def generate_answer_with_ai(
    prompt: str, messages: List[Dict[str, str]] = None, fast: bool = False
) -> str:
    contents = []
    if messages:
        for msg in messages:
            if msg["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
    system_prompt = f"""
あなたは佐賀大学のマスコット「カッチーくん」です。以下の設定で回答してください：

## キャラクター設定
- 佐賀大学のマスコットキャラクター
- 語尾はタイミングに応じて「カチ」を付ける
- 明るく答える

## 回答ルール
- 無闇にキャラクターを演出しようとせず、シンプルに答えてください
- 以下のシラバス情報を参考に、ユーザーの質問に答えてください
- 講義内容について答える時は、必ず提供されたシラバス情報のみを参照してください
- 一般知識や推測では絶対に答えないでください
- 回答は冗長にならないようにし、ユーザーの質問に的確に答えつつ、簡潔に回答してください
- マークダウン形式やマークダウン表形式、見出しなどを用いて、わかりやすく回答してください
- 情報が不足している場合は、検索結果について言及せず、より具体的な情報を求めてください
- 例：「どんな内容の講義について聞いているカチ？」「どんな分野の講義を探しているカチ？」

# シラバス情報
{prompt}
"""
    contents.append({"role": "user", "parts": [{"text": system_prompt}]})
    payload = {
        "contents": contents,
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


# ========================
#  チャットAPIサービス
# ========================
async def chat_service(request):
    question = request["question"]
    messages = request.get("messages", [])
    query_vector = await get_embedding_with_cohere(question)
    results = search_similar_syllabuses(query_vector, top_k=10)
    context_parts = []
    for row in results:
        code = row["code"]
        md = row["md"]
        lecture_info = get_lecture_by_code(code)
        if lecture_info:
            lecture_details = f"""
講義名: {lecture_info["name"] or "情報なし"}
講師: {lecture_info["lecturer"] or "情報なし"}
学年: {lecture_info["grade"] or "情報なし"}
曜日・校時: {lecture_info["time"] or "情報なし"}
"""
        else:
            lecture_details = "講義情報: 該当なし"
        context_parts.append(f"{lecture_details}\n\nシラバス内容:\n{md}")
    context = "\n\n---\n\n".join(context_parts)
    prompt = f"""
# シラバス情報
{context}

# ユーザーの質問
{question}
"""
    answer = await generate_answer_with_ai(prompt, messages, fast=True)

    async def gen():
        import re, asyncio

        for sentence in re.split(r"(。|！|!|\?|？)", answer):
            if sentence.strip():
                yield sentence
                await asyncio.sleep(0.05)

    return gen()


async def chat_service_stream(data):
    messages = data.get("messages", [])
    # ユーザー側のメッセージをすべて連結
    user_text = "\n".join([m["content"] for m in messages if m["role"] == "user"])
    question = data["question"]
    # 直近の質問がmessagesに含まれていない場合は追加
    if not messages or messages[-1]["content"] != question:
        user_text += ("\n" if user_text else "") + question
    query_vector = await get_embedding_with_cohere(user_text)
    results = search_similar_syllabuses(query_vector, top_k=10)
    context_parts = []
    for row in results:
        code = row["code"]
        md = row["md"]
        lecture_info = get_lecture_by_code(code)
        if lecture_info:
            lecture_details = f"""
講義名: {lecture_info["name"] or "情報なし"}
講師: {lecture_info["lecturer"] or "情報なし"}
学年: {lecture_info["grade"] or "情報なし"}
曜日・校時: {lecture_info["time"] or "情報なし"}
"""
        else:
            lecture_details = "講義情報: 該当なし"
        context_parts.append(f"{lecture_details}\n\nシラバス内容:\n{md}")
    context = "\n\n---\n\n".join(context_parts)
    prompt = f"# シラバス情報\n{context}\n\n# ユーザーの質問\n{question}"
    answer = await generate_answer_with_ai(prompt, messages, fast=True)
    for chunk in answer.split("。"):
        if chunk.strip():
            yield chunk + "。"
            await asyncio.sleep(0.05)


def bytes_to_float_list(byte_data: bytes) -> List[float]:
    count = len(byte_data) // 4  # float32 = 4バイト
    import struct

    return list(struct.unpack(f"{count}f", byte_data))


def cosine_similarity(a: List[float], b: List[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0


def get_available_lectures_service(day: str, period: int):
    """
    指定した曜日・時限に該当する講義一覧を返す
    day: "月", "火", ...
    period: 1, 2, ...
    """
    hankaku = "0123456789"
    zenkaku = "０１２３４５６７８９"
    period_zenkaku = "".join(
        zenkaku[hankaku.index(c)] if c in hankaku else c for c in str(period)
    )
    time_str = f"{day}{period_zenkaku}"
    return get_lectures_service(time=time_str)
