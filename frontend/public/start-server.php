<?php
// FastAPIサーバー起動スクリプト

// サーバーが既に起動しているかチェック
function isServerRunning() {
    $scriptPath = __DIR__ . '/check-server.sh';
    exec($scriptPath, $output, $returnCode);
    return $returnCode === 0;
}

// サーバーを起動
function startServer() {
    $scriptPath = __DIR__ . '/start-server.sh';
    
    // シェルスクリプトが存在するかチェック
    if (!file_exists($scriptPath)) {
        return ['success' => false, 'message' => 'start-server.shが見つかりません'];
    }
    
    // シェルスクリプトが実行可能かチェック
    if (!is_executable($scriptPath)) {
        return ['success' => false, 'message' => 'start-server.shに実行権限がありません。手動でchmod +x start-server.shを実行してください'];
    }
    
    // デバッグ情報を追加
    error_log("スクリプトパス: " . $scriptPath);
    error_log("スクリプト存在: " . (file_exists($scriptPath) ? 'true' : 'false'));
    error_log("スクリプト実行可能: " . (is_executable($scriptPath) ? 'true' : 'false'));
    error_log("現在のディレクトリ: " . getcwd());
    error_log("PATH: " . getenv('PATH'));
    
    // 環境変数を設定して実行
    $env = [
        'PATH' => '/usr/local/bin:/usr/bin:/bin',
        'HOME' => '/usr/home/s23238268',
        'USER' => 's23238268'
    ];
    
    // フルパスでshを指定して実行
    $command = "/bin/sh " . escapeshellarg($scriptPath);
    error_log("実行コマンド: " . $command);
    
    // 環境変数を設定して実行
    $descriptorspec = [
        0 => ["pipe", "r"],  // stdin
        1 => ["pipe", "w"],  // stdout
        2 => ["pipe", "w"]   // stderr
    ];
    
    $process = proc_open($command, $descriptorspec, $pipes, null, $env);
    
    if (is_resource($process)) {
        $output = stream_get_contents($pipes[1]);
        $error = stream_get_contents($pipes[2]);
        $returnCode = proc_close($process);
        
        error_log("exec出力: " . $output);
        error_log("execエラー: " . $error);
        error_log("リターンコード: " . $returnCode);
        
        if ($returnCode === 0) {
            return ['success' => true, 'message' => 'サーバーを起動しました'];
        } else {
            return ['success' => false, 'message' => 'サーバー起動に失敗しました', 'debug' => ['output' => $output, 'error' => $error, 'returnCode' => $returnCode]];
        }
    } else {
        return ['success' => false, 'message' => 'プロセスを開始できませんでした'];
    }
}

// メイン処理
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    header('Content-Type: application/json');
    
    if (!isServerRunning()) {
        $result = startServer();
        echo json_encode($result);
    } else {
        echo json_encode(['success' => true, 'message' => 'サーバーは既に起動しています']);
    }
} else {
    // GETリクエストの場合はサーバー状態を返す
    header('Content-Type: application/json');
    echo json_encode([
        'running' => isServerRunning(),
        'message' => isServerRunning() ? 'サーバーは起動中です' : 'サーバーは停止中です'
    ]);
}
?> 