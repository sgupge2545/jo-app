#!/home/s23238268/public_html/api/venv/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
import asyncio
from service import (
    get_lectures_service,
    get_syllabus_html_service,
    generate_page_with_ai,
    chat_service,
)


def print_json(obj, status=200):
    print("Content-Type: application/json")
    print()
    print(json.dumps(obj, ensure_ascii=False))


def print_text(text, status=200):
    print("Content-Type: text/plain; charset=utf-8")
    print()
    print(text)


def print_html(html, status=200):
    print("Content-Type: text/html; charset=utf-8")
    print()
    print(html)


def main():
    path = os.environ.get("PATH_INFO", "")
    method = os.environ.get("REQUEST_METHOD", "GET")
    query = {}
    if "QUERY_STRING" in os.environ:
        from urllib.parse import parse_qs

        query = {k: v[0] for k, v in parse_qs(os.environ["QUERY_STRING"]).items()}

    try:
        if method == "OPTIONS":
            print("Status: 204")
            print("Access-Control-Allow-Origin: *")
            print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
            print("Access-Control-Allow-Headers: Content-Type")
            print()
            return

        if path == "/lectures" and method == "GET":
            result = get_lectures_service(**query)
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
            print_json({"error": "Not Found"}, status=404)
    except Exception as e:
        print_json({"error": str(e)}, status=500)


if __name__ == "__main__":
    main()
