"use client";

import { useEffect, useState } from "react";

// データの型定義
interface PageData {
  title: string;
  html_content: string;
  css_content: string;
}

// デフォルトのシンプルなページデータ
const DEFAULT_PAGE_DATA: PageData = {
  title: "佐賀大学",
  html_content: `
    <header style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 30px; text-align: center; color: white;">
      <h1 style="margin: 0; font-size: 3rem; font-weight: bold;">佐賀大学</h1>
      <p style="font-size: 1.2rem; margin: 10px 0 0 0; opacity: 0.9;">Saga University</p>
      <p style="margin: 15px 0 0 0; font-size: 1rem;">地域と共に、未来を創造する</p>
    </header>
    
    <main style="max-width: 1200px; margin: 0 auto; padding: 40px 20px;">
      <section style="margin-bottom: 50px;">
        <h2 style="color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 15px;">大学概要</h2>
        <p style="font-size: 1.1rem; line-height: 1.8;">
          佐賀大学は、1949年に設立された国立大学法人です。佐賀県佐賀市に本部を置き、教育学部、経済学部、医学部、理工学部、農学部の5学部を擁し、
          地域社会の発展に貢献する人材の育成と、世界レベルの研究活動を行っています。
        </p>
      </section>
      
      <section style="margin-bottom: 50px;">
        <h2 style="color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 15px;">学部・研究科</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 30px;">
          <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; border-left: 5px solid #1e3c72;">
            <h3 style="color: #1e3c72; margin: 0 0 15px 0;">教育学部</h3>
            <p>教員養成を中心とした教育学部では、小学校・中学校・高等学校の教員を目指す学生が学んでいます。</p>
          </div>
          <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; border-left: 5px solid #1e3c72;">
            <h3 style="color: #1e3c72; margin: 0 0 15px 0;">経済学部</h3>
            <p>経済学・経営学の専門知識を身につけ、地域経済の発展に貢献できる人材を育成しています。</p>
          </div>
          <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; border-left: 5px solid #1e3c72;">
            <h3 style="color: #1e3c72; margin: 0 0 15px 0;">医学部</h3>
            <p>医学科と看護学科を設置し、地域医療の発展に貢献する医療人材を育成しています。</p>
          </div>
          <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; border-left: 5px solid #1e3c72;">
            <h3 style="color: #1e3c72; margin: 0 0 15px 0;">理工学部</h3>
            <p>工学・理学の分野で、次世代技術の開発と地域産業の発展に貢献する研究を行っています。</p>
          </div>
          <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; border-left: 5px solid #1e3c72;">
            <h3 style="color: #1e3c72; margin: 0 0 15px 0;">農学部</h3>
            <p>農業・生命科学の分野で、持続可能な農業と食料安全保障の実現を目指しています。</p>
          </div>
        </div>
      </section>
      
      <section style="margin-bottom: 50px;">
        <h2 style="color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 15px;">研究・国際交流</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px;">
          <div>
            <h3 style="color: #1e3c72;">特色ある研究</h3>
            <ul style="line-height: 1.8; padding-left: 20px;">
              <li>ナノテクノロジー・材料科学</li>
              <li>バイオテクノロジー・生命科学</li>
              <li>地域創生・地域経済</li>
              <li>教育・学習支援システム</li>
              <li>医療・健康科学</li>
            </ul>
          </div>
          <div>
            <h3 style="color: #1e3c72;">国際交流</h3>
            <ul style="line-height: 1.8; padding-left: 20px;">
              <li>海外大学との学術交流協定</li>
              <li>留学生の受け入れ・派遣</li>
              <li>国際共同研究プロジェクト</li>
              <li>英語教育プログラム</li>
              <li>グローバル人材育成</li>
            </ul>
          </div>
        </div>
      </section>
      
      <section style="margin-bottom: 50px;">
        <h2 style="color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 15px;">キャンパス情報</h2>
        <div style="background: #f0f8ff; padding: 30px; border-radius: 10px;">
          <h3 style="color: #1e3c72; margin: 0 0 20px 0;">本庄キャンパス（本部・教育学部・経済学部・理工学部・農学部）</h3>
          <p style="margin: 0 0 15px 0;"><strong>住所：</strong>〒840-8502 佐賀県佐賀市本庄町1</p>
          <p style="margin: 0 0 15px 0;"><strong>アクセス：</strong>JR佐賀駅からバス約15分</p>
          
          <h3 style="color: #1e3c72; margin: 30px 0 20px 0;">鍋島キャンパス（医学部）</h3>
          <p style="margin: 0 0 15px 0;"><strong>住所：</strong>〒849-8501 佐賀県佐賀市鍋島5-1-1</p>
          <p style="margin: 0;"><strong>アクセス：</strong>JR佐賀駅からバス約10分</p>
        </div>
      </section>
      
      <section style="text-align: center;">
        <h2 style="color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 15px;">お問い合わせ</h2>
        <p style="font-size: 1.1rem; margin-bottom: 30px;">入学に関するお問い合わせや、詳細な情報については以下までご連絡ください。</p>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
          <a href="/chat" style="display: inline-block; background: #1e3c72; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; transition: background-color 0.3s;">入学案内</a>
          <a href="/chat" style="display: inline-block; background: #2a5298; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; transition: background-color 0.3s;">研究情報</a>
          <a href="/chat" style="display: inline-block; background: #4a90e2; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; transition: background-color 0.3s;">国際交流</a>
        </div>
      </section>
    </main>
    
    <footer style="background: #333; color: white; text-align: center; padding: 30px; margin-top: 50px;">
      <div style="max-width: 1200px; margin: 0 auto;">
        <p style="margin: 0 0 15px 0; font-size: 1.1rem;">国立大学法人 佐賀大学</p>
        <p style="margin: 0 0 10px 0;">〒840-8502 佐賀県佐賀市本庄町1</p>
        <p style="margin: 0; opacity: 0.8;">&copy; 2024 Saga University. All rights reserved.</p>
      </div>
    </footer>
  `,
  css_content: `
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
      line-height: 1.6;
      color: #333;
      background: #fff;
    }
    
    h1, h2, h3 {
      color: #1e3c72;
      margin-bottom: 20px;
    }
    
    h1 {
      font-size: 2.5rem;
      margin-bottom: 10px;
    }
    
    h2 {
      font-size: 2rem;
      border-bottom: 2px solid #1e3c72;
      padding-bottom: 10px;
    }
    
    h3 {
      font-size: 1.3rem;
      color: #1e3c72;
    }
    
    p {
      font-size: 1.1rem;
      margin-bottom: 20px;
    }
    
    ul {
      padding-left: 20px;
    }
    
    li {
      margin-bottom: 10px;
    }
    
    a {
      color: #1e3c72;
      text-decoration: none;
      transition: all 0.3s ease;
    }
    
    a:hover {
      color: #2a5298;
      transform: translateY(-2px);
    }
    
    header a:hover {
      color: #fff;
      opacity: 0.8;
    }
    

    
    .grid-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 30px;
    }
    
    .card {
      background: #f8f9fa;
      padding: 25px;
      border-radius: 10px;
      border-left: 5px solid #1e3c72;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .card:hover {
      transform: translateY(-5px);
      box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    @media (max-width: 768px) {
      h1 {
        font-size: 2rem;
      }
      
      h2 {
        font-size: 1.5rem;
      }
      
      main {
        padding: 20px 15px;
      }
      
      .grid-container {
        grid-template-columns: 1fr;
      }
    }
  `,
};

export default function Home() {
  const [data, setData] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // ローカルストレージからページデータを取得
    const loadPageData = () => {
      try {
        const savedHtml = localStorage.getItem("html_content");
        const savedCss = localStorage.getItem("css_content");
        const savedTitle = localStorage.getItem("title");

        if (savedHtml && savedCss) {
          // 保存されたデータがある場合は復元
          const pageData: PageData = {
            title: savedTitle || "保存されたページ",
            html_content: savedHtml,
            css_content: savedCss,
          };
          setData(pageData);
          applyCSS(pageData.css_content);
        } else {
          // 初回訪問の場合はデフォルトページを表示・保存
          setData(DEFAULT_PAGE_DATA);
          applyCSS(DEFAULT_PAGE_DATA.css_content);

          // ローカルストレージに保存
          localStorage.setItem("html_content", DEFAULT_PAGE_DATA.html_content);
          localStorage.setItem("css_content", DEFAULT_PAGE_DATA.css_content);
          localStorage.setItem("title", DEFAULT_PAGE_DATA.title);
        }

        setLoading(false);
      } catch (error) {
        console.error("ローカルストレージの読み込みに失敗しました:", error);
        setError("ページの読み込みに失敗しました。");
        setLoading(false);
      }
    };

    loadPageData();
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

      {/* 固定のページ修正ツールリンク */}
      <div
        style={{
          position: "fixed",
          top: "20px",
          right: "20px",
          zIndex: 1000,
        }}
      >
        <a
          href="https://stuext.ai.is.saga-u.ac.jp/~s23238268/chat"
          style={{
            display: "inline-block",
            background: "rgba(255, 255, 255, 0.9)",
            color: "#1e3c72",
            padding: "12px 20px",
            textDecoration: "none",
            borderRadius: "25px",
            fontWeight: "bold",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            transition: "all 0.3s ease",
            backdropFilter: "blur(10px)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255, 255, 255, 1)";
            e.currentTarget.style.transform = "translateY(-2px)";
            e.currentTarget.style.boxShadow = "0 6px 20px rgba(0,0,0,0.2)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(255, 255, 255, 0.9)";
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
          }}
        >
          ✏️ ページ修正ツール
        </a>
      </div>

      {/* AIが生成したHTMLコンテンツを動的にレンダリング */}
      <div dangerouslySetInnerHTML={{ __html: data.html_content }} />
    </div>
  );
}
