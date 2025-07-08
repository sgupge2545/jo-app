<?php

// CORSヘッダーを設定
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

// OPTIONSリクエストの場合は早期リターン
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// GETリクエストのみ処理
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed', 'method' => $_SERVER['REQUEST_METHOD']]);
    exit;
}

// クエリパラメータを取得
$queryParams = $_GET;

// FastAPIサーバーにリクエストを転送
$url = 'http://127.0.0.1:8080/api/lectures';

// クエリパラメータがある場合はURLに追加
if (!empty($queryParams)) {
    $url .= '?' . http_build_query($queryParams);
}

$options = [
    'http' => [
        'header' => "Content-type: application/json\r\n",
        'method' => 'GET',
        'timeout' => 30
    ]
];

$context = stream_context_create($options);
$result = file_get_contents($url, false, $context);

if ($result === FALSE) {
    $error = error_get_last();
    
    http_response_code(500);
    echo json_encode(['error' => 'Failed to connect to API server', 'details' => $error]);
    exit;
}

// レスポンスをそのまま返す
echo $result;
?> 