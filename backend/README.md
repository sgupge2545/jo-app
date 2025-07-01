# JO App Backend API

FastAPI を使用したバックエンド API サーバーです。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. サーバーの起動

```bash
# 開発モードで起動（自動リロード有効）
python main.py

# または uvicorn を直接使用
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API エンドポイント

### 基本エンドポイント

- `GET /` - ルートエンドポイント
- `GET /health` - ヘルスチェック

### アイテム管理

- `GET /items` - アイテム一覧を取得
- `GET /items/{item_id}` - 特定のアイテムを取得
- `POST /items` - 新しいアイテムを作成
- `PUT /items/{item_id}` - アイテムを更新
- `DELETE /items/{item_id}` - アイテムを削除

### チャット機能

- `POST /chat` - メッセージを送信

## API ドキュメント

サーバー起動後、以下の URL で API ドキュメントにアクセスできます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 開発

### 環境変数

必要に応じて`.env`ファイルを作成して環境変数を設定してください。

### テスト

```bash
# テストを実行（テストファイルを作成後）
pytest
```

## デプロイ

本番環境では、適切な WSGI サーバー（Gunicorn 等）を使用してください：

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```
