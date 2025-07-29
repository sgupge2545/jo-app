<?php
$baseDir = "/usr/home";  // 実ファイルパス（FreeBSD系）
$baseUrl = "https://stuext.ai.is.saga-u.ac.jp/~";  // Webでアクセスする際のベースURL

// テンプレート読み込み（同じディレクトリに template.html がある前提）
$template = file_get_contents("template.html");

// HTMLの先頭と戻るボタンを出力
echo <<<HTML
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>ユーザーHP一覧</title>
  <style>
    body {
      font-family: sans-serif;
      margin: 80px 20px 40px 20px;
      background-color: #f8f9fa;
    }

    .back-button {
      position: fixed;
      top: 15px;
      left: 15px;
      padding: 10px 18px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      text-decoration: none;
      font-weight: bold;
      font-size: 14px;
      border-radius: 9999px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.3);
      z-index: 1000;
      transition: all 0.2s ease-in-out;
    }

    .back-button:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 12px rgba(0,0,0,0.35);
      opacity: 0.95;
    }

    h2 {
      margin-top: 60px;
      font-size: 20px;
    }
  </style>
</head>
<body>
  <a class="back-button" href="https://stuext.ai.is.saga-u.ac.jp/~s23238268/show_all_index.php">← 戻る</a>
HTML;

// ユーザー一覧から index.html を探す
foreach (scandir($baseDir) as $userDir) {
    if ($userDir === "." || $userDir === "..") continue;

    $publicHtmlPath = "$baseDir/$userDir/public_html/index.html";

    if (is_file($publicHtmlPath)) {
        // 表示URLを生成（例: https://.../~s23238268）
        $url = $baseUrl . $userDir;

        // テンプレートに埋め込んで出力
        $entryHtml = str_replace(
            ['{{user}}', '{{url}}'],
            [htmlspecialchars($userDir), htmlspecialchars($url)],
            $template
        );
        echo $entryHtml;
    }
}

// HTMLの終了
echo "</body></html>";
?>
