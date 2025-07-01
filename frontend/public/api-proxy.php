<?php
// デバッグ情報を有効化
error_reporting(E_ALL);
ini_set('display_errors', 1);

// CORSヘッダーを設定
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

// デバッグログ
error_log("API Proxy accessed. Method: " . $_SERVER['REQUEST_METHOD']);

// OPTIONSリクエストの場合は早期リターン
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    error_log("OPTIONS request received");
    exit(0);
}

// POSTリクエストのみ処理
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    error_log("Invalid method: " . $_SERVER['REQUEST_METHOD']);
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed', 'method' => $_SERVER['REQUEST_METHOD']]);
    exit;
}

// リクエストボディを取得
$input = file_get_contents('php://input');
error_log("Request body: " . $input);

$data = json_decode($input, true);

if (!$data || !isset($data['prompt'])) {
    error_log("Invalid request data");
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request data', 'received' => $data]);
    exit;
}

// FastAPIサーバーにリクエストを転送
$url = 'http://localhost:8080/api/generate-page';
error_log("Forwarding to: " . $url);

$options = [
    'http' => [
        'header' => "Content-type: application/json\r\n",
        'method' => 'POST',
        'content' => $input,
        'timeout' => 60
    ]
];

$context = stream_context_create($options);
$result = file_get_contents($url, false, $context);

if ($result === FALSE) {
    $error = error_get_last();
    error_log("Failed to connect to API server: " . print_r($error, true));
    http_response_code(500);
    echo json_encode(['error' => 'Failed to connect to API server', 'details' => $error]);
    exit;
}

error_log("API response received: " . substr($result, 0, 200));

// レスポンスをそのまま返す
echo $result;
?> 