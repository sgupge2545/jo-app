<?php
// クライアントからのリクエストボディを取得
$input = file_get_contents('php://input');

// FastAPIのエンドポイント
$backend_url = 'http://localhost:8080/api/chat';

// HTTPコンテキストを作成
$context = stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\n",
        'content' => $input,
        'timeout' => 60
    ]
]);

// レスポンス用ヘッダ
header('Content-Type: text/plain');
header('Cache-Control: no-cache');

// リクエスト実行
$response = file_get_contents($backend_url, false, $context);

if ($response === false) {
    http_response_code(500);
    echo "バックエンドAPIへの接続に失敗しました";
} else {
    echo $response;
}
?>