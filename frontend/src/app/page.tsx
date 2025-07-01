"use client";

import { useEffect, useState } from "react";

// データの型定義
interface PageData {
  title: string;
  html_content: string;
  css_content: string;
}

export default function Home() {
  const [data, setData] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/page")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((pageData: PageData) => {
        setData(pageData);
        setLoading(false);

        // CSSを動的に適用
        applyCSS(pageData.css_content);
      })
      .catch((error) => {
        console.error("データの取得に失敗しました:", error);
        setError(
          "データの読み込みに失敗しました。APIサーバーが起動しているか確認してください。"
        );
        setLoading(false);
      });
  }, []);

  // CSSを動的に適用する関数
  const applyCSS = (cssContent: string) => {
    // 既存のスタイルタグを削除
    const existingStyle = document.getElementById("dynamic-css");
    if (existingStyle) {
      existingStyle.remove();
    }

    // 新しいスタイルタグを作成
    const style = document.createElement("style");
    style.id = "dynamic-css";
    style.textContent = cssContent;
    document.head.appendChild(style);
  };

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          fontSize: "1.2rem",
        }}
      >
        ページを読み込み中...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        <h1>エラー</h1>
        <p>{error}</p>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: "10px 20px",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          再読み込み
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div>
      {/* タイトルをページタイトルとして設定 */}
      <title>{data.title}</title>

      {/* AIが生成したHTMLコンテンツを動的にレンダリング */}
      <div dangerouslySetInnerHTML={{ __html: data.html_content }} />
    </div>
  );
}
