#!/home/s23238268/public_html/venv/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
import cgi
import cgitb
cgitb.enable()
import asyncio
from service import (
    get_lectures_service,
    get_syllabus_html_service,
    generate_page_with_ai,
    chat_service,
)

def print_json(obj, status=200):
    print(f"Status: {status}")
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()
    print(json.dumps(obj, ensure_ascii=False))

def print_text(text, status=200):
    print(f"Status: {status}")
    print("Content-Type: text/plain; charset=utf-8")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()
    print(text)

def print_html(html, status=200):
    print(f"Status: {status}")
    print("Content-Type: text/html; charset=utf-8")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()
    print(html)

def main():
    path = os.environ.get("PATH_INFO", "")
    method = os.environ.get("REQUEST_METHOD", "GET")
    form = cgi.FieldStorage()

    try:
        if method == "OPTIONS":
            print("Status: 204")
            print("Access-Control-Allow-Origin: *")
            print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
            print("Access-Control-Allow-Headers: Content-Type")
            print()
            return

        if path == "/lectures" and method == "GET":
            params = {k: form.getvalue(k) for k in form.keys()}
            result = get_lectures_service(**params)
            print_json(result)
        elif path.startswith("/syllabuses/") and method == "GET":
            code = path.split("/")[-1]
            html = get_syllabus_html_service(code)
            print_html(html)
        elif path == "/generate-page" and method == "POST":
            data = json.load(sys.stdin)
            result = asyncio.run(generate_page_with_ai(data["prompt"]))
            print_json(result)
        elif path == "/chat" and method == "POST":
            data = json.load(sys.stdin)
            # chat_serviceはStreamingResponseを返すのでtextとして出力
            resp = asyncio.run(chat_service(data))
            # StreamingResponseのbody_iteratorをテキストとして出力
            if hasattr(resp, 'body_iterator'):
                text = "".join([chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in resp.body_iterator])
            else:
                text = str(resp)
            print_text(text)
        else:
            print_json({"error": "Not Found"}, status=404)
    except Exception as e:
        print_json({"error": str(e)}, status=500)

if __name__ == "__main__":
    main() 