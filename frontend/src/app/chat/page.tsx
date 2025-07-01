"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

interface PageData {
  title: string;
  html_content: string;
  css_content: string;
}

export default function ChatPage() {
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 初期化時に現在のページデータを読み込み
  useEffect(() => {
    const loadCurrentPage = () => {
      try {
        const savedHtml = localStorage.getItem("html_content");
        const savedCss = localStorage.getItem("css_content");
        const savedTitle = localStorage.getItem("title");

        if (savedHtml && savedCss) {
          const pageData: PageData = {
            title: savedTitle || "現在のページ",
            html_content: savedHtml,
            css_content: savedCss,
          };
          setCurrentPage(pageData);
          applyCSS(pageData.css_content);
        }
      } catch (error) {
        console.error("現在のページデータの読み込みに失敗しました:", error);
      }
    };

    loadCurrentPage();
  }, []);

  // CSSを動的に適用する関数
  const applyCSS = (cssContent: string) => {
    const existingStyle = document.getElementById("dynamic-css");
    if (existingStyle) {
      existingStyle.remove();
    }

    const style = document.createElement("style");
    style.id = "dynamic-css";
    style.textContent = cssContent;
    document.head.appendChild(style);
  };

  // ページを修正
  const modifyPage = async () => {
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // 現在のページ情報を取得
      const currentHtml = localStorage.getItem("html_content") || "";
      const currentCss = localStorage.getItem("css_content") || "";
      const currentTitle = localStorage.getItem("title") || "";

      // 現在のページ情報を含めたプロンプトを作成
      const enhancedPrompt = `
現在のページ情報:
タイトル: ${currentTitle}

HTML内容:
${currentHtml}

CSS内容:
${currentCss}

修正要求: ${prompt}

上記の現在のページに対して、修正要求に従ってページを修正してください。
`;

      const response = await fetch("/~s23238268/api-proxy.php", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: enhancedPrompt }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const pageData: PageData = await response.json();
      setCurrentPage(pageData);
      applyCSS(pageData.css_content);

      // ローカルストレージに保存
      localStorage.setItem("html_content", pageData.html_content);
      localStorage.setItem("css_content", pageData.css_content);
      localStorage.setItem("title", pageData.title);

      setPrompt(""); // プロンプトをクリア
    } catch (error) {
      console.error("ページ修正エラー:", error);
      setError("ページの修正に失敗しました。もう一度お試しください。");
    } finally {
      setIsLoading(false);
    }
  };

  // Enterキーで送信
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      modifyPage();
    }
  };

  return (
    <div className="page-container">
      <div className="header">
        <h1>AIページ修正ツール</h1>
        <p>プロンプトを入力して、ページを修正してください</p>
        <Link href="/" className="back-link">
          ← TOPページに戻る
        </Link>
      </div>

      <div className="input-section">
        <div className="input-container">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="例: 色を青系に変更してください、フォントサイズを大きくしてください、レイアウトを2カラムにしてください...（現在のページを基に修正されます）"
            disabled={isLoading}
            className="prompt-input"
          />
          <button
            onClick={modifyPage}
            disabled={!prompt.trim() || isLoading}
            className="modify-button"
          >
            {isLoading ? "修正中..." : "ページを修正"}
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}
      </div>

      <div className="preview-section">
        <h3>ページプレビュー</h3>
        {isLoading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>ページを修正中...</p>
          </div>
        ) : currentPage ? (
          <div className="preview-content">
            <div
              dangerouslySetInnerHTML={{ __html: currentPage.html_content }}
            />
          </div>
        ) : (
          <div className="preview-placeholder">
            <p>
              プロンプトを入力してページを修正すると、ここにプレビューが表示されます
            </p>
          </div>
        )}
      </div>

      <style jsx>{`
        .page-container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          min-height: 100vh;
        }

        .header {
          text-align: center;
          margin-bottom: 30px;
        }

        .header h1 {
          color: #333;
          margin-bottom: 10px;
          font-size: 2.5rem;
        }

        .header p {
          color: #666;
          font-size: 1.1rem;
          margin-bottom: 15px;
        }

        .back-link {
          display: inline-block;
          color: #007bff;
          text-decoration: none;
          font-weight: bold;
          padding: 8px 16px;
          border: 2px solid #007bff;
          border-radius: 6px;
          transition: all 0.3s ease;
        }

        .back-link:hover {
          background: #007bff;
          color: white;
        }

        .input-section {
          margin-bottom: 30px;
        }

        .input-container {
          display: flex;
          gap: 15px;
          margin-bottom: 15px;
        }

        .prompt-input {
          flex: 1;
          padding: 15px;
          border: 2px solid #e0e0e0;
          border-radius: 10px;
          resize: vertical;
          min-height: 80px;
          font-family: inherit;
          font-size: 1rem;
          transition: border-color 0.3s ease;
        }

        .prompt-input:focus {
          outline: none;
          border-color: #007bff;
        }

        .prompt-input:disabled {
          background-color: #f5f5f5;
          cursor: not-allowed;
        }

        .modify-button {
          padding: 15px 30px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          font-size: 1rem;
          font-weight: bold;
          transition: background 0.3s ease;
          white-space: nowrap;
        }

        .modify-button:hover:not(:disabled) {
          background: #0056b3;
        }

        .modify-button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .error-message {
          background: #f8d7da;
          color: #721c24;
          padding: 15px;
          border-radius: 8px;
          border: 1px solid #f5c6cb;
        }

        .preview-section {
          border: 2px solid #e0e0e0;
          border-radius: 15px;
          background: white;
          overflow: hidden;
        }

        .preview-section h3 {
          padding: 20px;
          margin: 0;
          border-bottom: 1px solid #e0e0e0;
          color: #333;
          background: #f8f9fa;
        }

        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          min-height: 400px;
          background: #f8f9fa;
        }

        .loading-spinner {
          width: 48px;
          height: 48px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #007bff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }

        .loading-container p {
          color: #666;
          font-size: 1.1rem;
          margin: 0;
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        .preview-content {
          min-height: 400px;
        }

        .preview-placeholder {
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666;
          text-align: center;
          padding: 60px 20px;
          min-height: 400px;
          background: #f8f9fa;
        }

        @media (max-width: 768px) {
          .input-container {
            flex-direction: column;
          }

          .modify-button {
            width: 100%;
          }

          .header h1 {
            font-size: 2rem;
          }
        }
      `}</style>
    </div>
  );
}
