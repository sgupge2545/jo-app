from fastapi import FastAPI, Query
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
