<?php
// CORSヘッダーを設定
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: text/html; charset=UTF-8');

// OPTIONSリクエストの場合は早期リターン
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// GETリクエストのみ処理
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo 'Method not allowed';
    exit;
}

// codeパラメータを取得
if (!isset($_GET['code']) || empty($_GET['code'])) {
    http_response_code(400);
    echo 'Missing code parameter';
    exit;
}
$code = urlencode($_GET['code']);

// FastAPIサーバーにリクエストを転送
$url = 'http://127.0.0.1:8080/api/syllabuses/' . $code;

$options = [
    'http' => [
        'header' => "Content-type: text/html\r\n",
        'method' => 'GET',
        'timeout' => 30
    ]
];
$context = stream_context_create($options);
$result = file_get_contents($url, false, $context);

if ($result === FALSE) {
    $error = error_get_last();
    http_response_code(500);
    echo 'Failed to connect to API server';
    exit;
}

// HTMLをそのまま返す
echo $result;
