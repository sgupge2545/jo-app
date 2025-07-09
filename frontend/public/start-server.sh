#!/bin/sh

# FastAPIサーバー起動スクリプト

# デバッグ情報を出力（apiディレクトリに作成）
SCRIPT_DIR="$(dirname "$0")"
DEBUG_LOG="$SCRIPT_DIR/api/debug.log"
echo "スクリプト開始: $(date)" >> "$DEBUG_LOG"
echo "現在のディレクトリ: $(pwd)" >> "$DEBUG_LOG"
echo "スクリプトディレクトリ: $SCRIPT_DIR" >> "$DEBUG_LOG"
echo "PATH: $PATH" >> "$DEBUG_LOG"
echo "ユーザー: $(whoami)" >> "$DEBUG_LOG"

# バックエンドディレクトリに移動
echo "ディレクトリ移動開始" >> "$DEBUG_LOG"
cd "$SCRIPT_DIR/api"
echo "移動後のディレクトリ: $(pwd)" >> "$DEBUG_LOG"

# 仮想環境の存在確認
echo "仮想環境確認開始" >> "$DEBUG_LOG"
if [ ! -f "./venv/bin/activate" ]; then
    echo "仮想環境が見つかりません" >> "$DEBUG_LOG"
    exit 1
fi
echo "仮想環境確認完了" >> "$DEBUG_LOG"

# 仮想環境をアクティベートしてサーバーを起動
echo "仮想環境アクティベート開始" >> "$DEBUG_LOG"
. ./venv/bin/activate
echo "仮想環境アクティベート完了" >> "$DEBUG_LOG"

# Pythonのバージョン確認
echo "Pythonバージョン確認開始" >> "$DEBUG_LOG"
python3 --version >> "$DEBUG_LOG" 2>&1
echo "Pythonバージョン確認完了" >> "$DEBUG_LOG"

# hypercornの存在確認
echo "hypercorn確認開始" >> "$DEBUG_LOG"
python3 -c "import hypercorn" >> "$DEBUG_LOG" 2>&1
echo "hypercorn確認完了" >> "$DEBUG_LOG"

# サーバーを起動
echo "サーバー起動開始" >> "$DEBUG_LOG"
nohup python3 -m hypercorn main:app --bind 0.0.0.0:8080 --reload > app.log 2>&1 &
echo "nohupコマンド実行完了" >> "$DEBUG_LOG"

# プロセスIDを保存
echo $! > server.pid
echo "プロセスID: $!" >> "$DEBUG_LOG"
echo "server.pidファイル作成完了" >> "$DEBUG_LOG"

echo "サーバーを起動しました (PID: $!)" 