<?php
// SSE用ヘッダを設定
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');
header('Connection: keep-alive');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');

// バッファリングを無効化
if (ob_get_level()) ob_end_clean();

// クライアントからのリクエストボディを取得
$input = file_get_contents('php://input');

// FastAPIのSSEエンドポイント
$backend_url = 'http://localhost:8080/api/chat-sse';

// HTTPコンテキストを作成
$context = stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\n",
        'content' => $input,
        'timeout' => 60
    ]
]);

// ストリーミングでレスポンスを読み取り
$handle = fopen($backend_url, 'r', false, $context);

if ($handle) {
    while (!feof($handle)) {
        $line = fgets($handle);
        if ($line !== false) {
            echo $line;
            flush();
        }
    }
    fclose($handle);
} else {
    echo "data: エラーが発生しました\n\n";
}
?> 