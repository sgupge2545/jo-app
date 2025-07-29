<?php
$baseDir = "/usr/home";
$baseUrl = "https://stuext.ai.is.saga-u.ac.jp/~";
$template = file_get_contents("template.html");

// ページネーション設定
$itemsPerPage = 10;
$currentPage = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;

// ユーザーデータを収集
$allUsers = [];
$entries = scandir($baseDir);
foreach ($entries as $userDir) {
    if (!preg_match('/^s\d{8}$/', $userDir)) continue;

    $publicHtmlDir = "$baseDir/$userDir/public_html";
    if (!is_dir($publicHtmlDir)) continue;

    $found = false;
    $url = null;

    try {
        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($publicHtmlDir, FilesystemIterator::SKIP_DOTS),
            RecursiveIteratorIterator::SELF_FIRST
        );

        $fallback = null;

        foreach ($iterator as $file) {
            $filename = strtolower($file->getFilename());

            if ($filename === "index.html") {
                $relPath = str_replace("$publicHtmlDir/", '', $file->getPathname());
                $url = $baseUrl . $userDir . "/" . $relPath;
                $found = true;
                break;
            } elseif (str_ends_with($filename, ".html") && !$fallback) {
                $relPath = str_replace("$publicHtmlDir/", '', $file->getPathname());
                $fallback = $baseUrl . $userDir . "/" . $relPath;
            }
        }

        if (!$found && $fallback) {
            $url = $fallback;
            $found = true;
        }

        if ($found) {
            $allUsers[] = [
                'user' => substr($userDir, 1),
                'url' => $url
            ];
        }

    } catch (UnexpectedValueException $e) {
        continue;
    }
}

// ページネーション計算
$totalUsers = count($allUsers);
$totalPages = ceil($totalUsers / $itemsPerPage);
$startIndex = ($currentPage - 1) * $itemsPerPage;
$endIndex = min($startIndex + $itemsPerPage, $totalUsers);
$currentUsers = array_slice($allUsers, $startIndex, $itemsPerPage);

// HTML全体と戻るボタン
echo <<<HTML
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>ユーザーHP一覧</title>
  <style>
    body {
      font-family: sans-serif;
      margin: 0px 20px 40px 20px;
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

    .pagination {
      display: flex;
      justify-content: center;
      align-items: center;
      margin: 40px 0;
      gap: 10px;
    }

    .pagination a, .pagination span {
      padding: 10px 15px;
      text-decoration: none;
      border-radius: 5px;
      font-weight: bold;
      transition: all 0.2s ease;
    }

    .pagination a {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .pagination a:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }

    .pagination .current {
      background: #e9ecef;
      color: #495057;
      cursor: default;
    }

    .pagination .disabled {
      background: #f8f9fa;
      color: #adb5bd;
      cursor: not-allowed;
    }

    h2 {
      margin-top: 60px;
      font-size: 20px;
    }
  </style>
</head>
<body>
  <a class="back-button" href="https://stuext.ai.is.saga-u.ac.jp/~s23238268/">← 戻る</a>
HTML;

// ページネーション生成関数
function generatePagination($currentPage, $totalPages) {
    if ($totalPages <= 1) return '';
    
    $html = '<div class="pagination">';
    
    // 前のページ
    if ($currentPage > 1) {
        $html .= '<a href="?page=' . ($currentPage - 1) . '">← 前へ</a>';
    } else {
        $html .= '<span class="disabled">← 前へ</span>';
    }
    
    // ページ番号
    $startPage = max(1, $currentPage - 2);
    $endPage = min($totalPages, $currentPage + 2);
    
    if ($startPage > 1) {
        $html .= '<a href="?page=1">1</a>';
        if ($startPage > 2) {
            $html .= '<span>...</span>';
        }
    }
    
    for ($i = $startPage; $i <= $endPage; $i++) {
        if ($i == $currentPage) {
            $html .= '<span class="current">' . $i . '</span>';
        } else {
            $html .= '<a href="?page=' . $i . '">' . $i . '</a>';
        }
    }
    
    if ($endPage < $totalPages) {
        if ($endPage < $totalPages - 1) {
            $html .= '<span>...</span>';
        }
        $html .= '<a href="?page=' . $totalPages . '">' . $totalPages . '</a>';
    }
    
    // 次のページ
    if ($currentPage < $totalPages) {
        $html .= '<a href="?page=' . ($currentPage + 1) . '">次へ →</a>';
    } else {
        $html .= '<span class="disabled">次へ →</span>';
    }
    
    $html .= '</div>';
    return $html;
}

// 上部ページネーション
echo generatePagination($currentPage, $totalPages);

// 現在のページのユーザーを表示
foreach ($currentUsers as $userData) {
    $entryHtml = str_replace(
        ['{{user}}', '{{url}}'],
        [htmlspecialchars($userData['user']), htmlspecialchars($userData['url'])],
        $template
    );
    echo $entryHtml;
}

// 下部ページネーション
echo generatePagination($currentPage, $totalPages);

echo "</body></html>";
?>
