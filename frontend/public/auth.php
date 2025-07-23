<?php
session_start();

// CORSヘッダーを設定
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

// OPTIONSリクエストの場合は早期リターン
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// Azure Entra ID設定（環境変数から読み込み）
$tenantId = getenv('MS_TENANT_ID');
$clientId = getenv('MS_CLIENT_ID');
$clientSecret = getenv('MS_CLIENT_SECRET');
$redirectUri = getenv('MS_REDIRECT_URI');

// 認証エンドポイント
$authUrl = "https://login.microsoftonline.com/{$tenantId}/oauth2/v2.0/authorize";
$tokenUrl = "https://login.microsoftonline.com/{$tenantId}/oauth2/v2.0/token";

// GETリクエストの処理
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $action = $_GET['action'] ?? '';
    
    switch ($action) {
        case 'login':
            handleLogin();
            break;
        case 'callback':
            handleCallback();
            break;
        case 'logout':
            handleLogout();
            break;
        case 'check':
            checkAuth();
            break;
        default:
            checkAuth();
    }
}

// POSTリクエストの処理
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if (!$data || !isset($data['action'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid request']);
        exit;
    }
    
    switch ($data['action']) {
        case 'check':
            checkAuth();
            break;
        case 'logout':
            handleLogout();
            break;
        default:
            http_response_code(400);
            echo json_encode(['error' => 'Invalid action']);
            exit;
    }
}

function handleLogin() {
    global $authUrl, $clientId, $redirectUri;
    
    // リダイレクト先を取得
    $redirect = $_GET['redirect'] ?? '/~s23238268/';
    $_SESSION['post_auth_redirect'] = $redirect;
    
    $state = bin2hex(random_bytes(16));
    $_SESSION['oauth_state'] = $state;
    
    $params = [
        'client_id' => $clientId,
        'response_type' => 'code',
        'redirect_uri' => $redirectUri . '?action=callback',
        'scope' => 'openid profile email',
        'state' => $state,
        'response_mode' => 'query'
    ];
    
    $url = $authUrl . '?' . http_build_query($params);
    
    // 直接リダイレクト
    header('Location: ' . $url);
    exit;
}

function handleCallback() {
    global $tokenUrl, $clientId, $clientSecret, $redirectUri;
    
    $code = $_GET['code'] ?? '';
    $state = $_GET['state'] ?? '';
    
    // ステート検証
    if (!isset($_SESSION['oauth_state']) || $_SESSION['oauth_state'] !== $state) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid state parameter']);
        exit;
    }
    
    // アクセストークンを取得
    $tokenData = [
        'client_id' => $clientId,
        'client_secret' => $clientSecret,
        'code' => $code,
        'grant_type' => 'authorization_code',
        'redirect_uri' => $redirectUri . '?action=callback'
    ];
    
    // file_get_contents()を使用
    $options = [
        'http' => [
            'header' => "Content-type: application/x-www-form-urlencoded\r\n",
            'method' => 'POST',
            'content' => http_build_query($tokenData),
            'timeout' => 30
        ]
    ];
    
    $context = stream_context_create($options);
    $response = file_get_contents($tokenUrl, false, $context);
    
    if ($response === FALSE) {
        http_response_code(400);
        echo json_encode(['error' => 'Failed to get access token']);
        exit;
    }
    
    $tokenInfo = json_decode($response, true);
    
    // IDトークンからユーザー情報を取得
    $idToken = $tokenInfo['id_token'];
    $userInfo = decodeJWT($idToken);
    
    // ユーザー情報を送信
    $url = 'https://stuext.ai.is.saga-u.ac.jp/~s23238268/api/auth/login';
    $userData = [
        'uid' => $userInfo['sub'],
        'name' => $userInfo['name'] ?? $userInfo['email'],
        'email' => $userInfo['email']
    ];
    
    $apiOptions = [
        'http' => [
            'header' => "Content-Type: application/json\r\n",
            'method' => 'POST',
            'content' => json_encode($userData),
            'timeout' => 30
        ]
    ];
    
    $apiContext = stream_context_create($apiOptions);
    $response = file_get_contents($url, false, $apiContext);
    
    if ($response !== FALSE) {
        $user = json_decode($response, true);
        // ユーザーIDをセッションに保存
        $_SESSION['user_id'] = $user['id'];
    }
    
    // セッションに保存
    $_SESSION['username'] = $userInfo['name'] ?? $userInfo['email'];
    $_SESSION['email'] = $userInfo['email'];
    $_SESSION['logged_in'] = true;
    $_SESSION['login_time'] = time();
    $_SESSION['access_token'] = $tokenInfo['access_token'];
    
    // 認証後にリダイレクト
    $redirect = $_SESSION['post_auth_redirect'] ?? '/~s23238268/';
    unset($_SESSION['post_auth_redirect']); // セッションから削除
    
    header('Location: ' . $redirect);
    exit;
}

function handleLogout() {
    global $tenantId;
    
    // セッションを破棄
    session_destroy();
    
    // Azure Entra IDのログアウトURLにリダイレクト
    $logoutUrl = "https://login.microsoftonline.com/{$tenantId}/oauth2/v2.0/logout";
    $postLogoutRedirectUri = "https://stuext.ai.is.saga-u.ac.jp/~s23238268/";
    
    $logoutParams = [
        'post_logout_redirect_uri' => $postLogoutRedirectUri
    ];
    
    $fullLogoutUrl = $logoutUrl . '?' . http_build_query($logoutParams);
    
    header('Location: ' . $fullLogoutUrl);
    exit;
}

function checkAuth() {
    if (isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true) {
        // 認証済みの場合、PythonのAPIでユーザー情報を同期
        if (!isset($_SESSION['user_id']) || empty($_SESSION['user_id'])) {
            $url = 'https://stuext.ai.is.saga-u.ac.jp/~s23238268/api/auth/login';
            $userData = [
                'uid' => $_SESSION['user_id'] ?? '',  // 元のMicrosoft UID
                'name' => $_SESSION['username'],
                'email' => $_SESSION['email']
            ];
            
            $apiOptions = [
                'http' => [
                    'header' => "Content-Type: application/json\r\n",
                    'method' => 'POST',
                    'content' => json_encode($userData),
                    'timeout' => 30
                ]
            ];
            
            $apiContext = stream_context_create($apiOptions);
            $response = file_get_contents($url, false, $apiContext);
            
            if ($response !== FALSE) {
                $user = json_decode($response, true);
                $_SESSION['user_id'] = $user['id'];
            }
        }
        
        echo json_encode([
            'authenticated' => true,
            'user' => [
                'id' => $_SESSION['user_id'],
                'username' => $_SESSION['username'],
                'email' => $_SESSION['email'],
                'login_time' => $_SESSION['login_time']
            ]
        ]);
    } else {
        http_response_code(401);
        echo json_encode([
            'authenticated' => false,
            'error' => 'Not authenticated'
        ]);
    }
}

function decodeJWT($token) {
    $parts = explode('.', $token);
    if (count($parts) !== 3) {
        return null;
    }
    
    $payload = $parts[1];
    $payload = str_replace(['-', '_'], ['+', '/'], $payload);
    $payload = base64_decode($payload);
    
    return json_decode($payload, true);
}
?> 