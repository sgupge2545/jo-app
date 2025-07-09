#!/bin/sh

# FastAPIサーバー状態確認スクリプト

# バックエンドディレクトリに移動
cd "$(dirname "$0")/api"

# PIDファイルが存在する場合、プロセスを確認
if [ -f server.pid ]; then
    PID=$(cat server.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "サーバーは起動中です (PID: $PID)"
        exit 0
    else
        echo "プロセス $PID は停止しています"
        rm server.pid
        exit 1
    fi
else
    echo "サーバーは停止中です"
    exit 1
fi 