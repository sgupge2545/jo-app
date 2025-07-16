<?php
// クライアントからのリクエストボディを取得
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// FastAPIのエンドポイント
$backend_url = 'http://localhost:8080/api/chat';

// リクエストデータを準備（questionとmessagesの両方を送信）
$request_data = [
    'question' => $data['question'] ?? '',
    'messages' => $data['messages'] ?? []
];

// HTTPコンテキストを作成
$context = stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\n",
        'content' => json_encode($request_data),
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