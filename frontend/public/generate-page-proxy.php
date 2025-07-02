<?php


// CORSヘッダーを設定
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

// OPTIONSリクエストの場合は早期リターン
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {

    exit(0);
}

// POSTリクエストのみ処理
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {

    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed', 'method' => $_SERVER['REQUEST_METHOD']]);
    exit;
}

// リクエストボディを取得
$input = file_get_contents('php://input');


$data = json_decode($input, true);

if (!$data || !isset($data['prompt'])) {

    http_response_code(400);
    echo json_encode(['error' => 'Invalid request data', 'received' => $data]);
    exit;
}

// FastAPIサーバーにリクエストを転送
$url = 'http://127.0.0.1:8080/api/generate-page';


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

    http_response_code(500);
    echo json_encode(['error' => 'Failed to connect to API server', 'details' => $error]);
    exit;
}



// レスポンスをそのまま返す
echo $result;
?> 