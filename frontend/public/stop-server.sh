#!/bin/sh

# FastAPIサーバー停止スクリプト

# バックエンドディレクトリに移動
cd "$(dirname "$0")/api"

# PIDファイルが存在する場合、プロセスを停止
if [ -f server.pid ]; then
    PID=$(cat server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        rm server.pid
        echo "サーバーを停止しました (PID: $PID)"
    else
        echo "プロセス $PID は既に停止しています"
        rm server.pid
    fi
else
    echo "PIDファイルが見つかりません"
fi 