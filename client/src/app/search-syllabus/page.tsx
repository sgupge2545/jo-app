"use client";

import { useState, useEffect } from "react";

interface Lecture {
  id: number;
  title?: string;
  category?: string;
  code?: string;
  name?: string;
  lecturer?: string;
  grade?: string;
  class_name?: string;
  season?: string;
  time?: string;
}

interface User {
  id: string;
  username: string;
  email: string;
  login_time: number;
}

export default function SearchSyllabus() {
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalHtml, setModalHtml] = useState<string | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || "";
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";

  // 認証状態をチェック
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/auth?action=check`);
        if (response.ok) {
          const authData = await response.json();
          if (authData.authenticated) {
            setUser(authData.user);
          } else {
            window.location.href = `${FRONTEND_URL}/auth?action=login&redirect=${FRONTEND_URL}/search-syllabus`;
            return;
          }
        } else {
          window.location.href = `${FRONTEND_URL}/auth?action=login&redirect=${FRONTEND_URL}/search-syllabus`;
          return;
        }
      } catch (error) {
        console.error("認証チェックエラー:", error);
        window.location.href = `${FRONTEND_URL}/auth?action=login&redirect=${FRONTEND_URL}/search-syllabus`;
        return;
      } finally {
        setAuthLoading(false);
      }
    };

    checkAuth();
  }, []);

  // 検索フィルター
  const [filters, setFilters] = useState({
    title: "",
    category: "",
    code: "",
    name: "",
    lecturer: "",
    grade: "",
    class_name: "",
    season: "",
    time: "",
    keyword: "",
  });

  // 講義データを取得
  const fetchLectures = async (searchParams: Record<string, string> = {}) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await fetch(
        `${BACKEND_URL}/lectures?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setLectures(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "データの取得に失敗しました"
      );
    } finally {
      setLoading(false);
    }
  };

  // 検索実行
  const handleSearch = () => {
    const nonEmptyFilters = Object.fromEntries(
      Object.entries(filters).filter(([, value]) => value.trim() !== "")
    );
    setHasSearched(true);
    fetchLectures(nonEmptyFilters);
  };

  // フィルターリセット
  const handleReset = () => {
    setFilters({
      title: "",
      category: "",
      code: "",
      name: "",
      lecturer: "",
      grade: "",
      class_name: "",
      season: "",
      time: "",
      keyword: "",
    });
    setLectures([]);
    setHasSearched(false);
  };

  // 講義カードクリック時のハンドラ
  const handleLectureClick = async (code: string) => {
    setModalOpen(true);
    setModalHtml(null);
    setModalLoading(true);
    setModalError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/syllabuses/${code}`);
      if (!res.ok) throw new Error("シラバスの取得に失敗しました");
      const html = await res.text();
      setModalHtml(html);
    } catch (e) {
      setModalError(e instanceof Error ? e.message : "エラーが発生しました");
    } finally {
      setModalLoading(false);
    }
  };

  // 認証中はローディング表示
  if (authLoading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          fontSize: "1.2rem",
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        }}
      >
        認証を確認中...
      </div>
    );
  }

  // 未認証の場合は何も表示しない（リダイレクト中）
  if (!user) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          fontSize: "1.2rem",
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        }}
      >
        認証を確認中...
      </div>
    );
  }

  return (
    <div
      style={{
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      {/* ヘッダー */}
      <header
        style={{
          background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
          color: "white",
          padding: "30px 20px",
          textAlign: "center",
          position: "relative",
        }}
      >
        {/* 左上のトップページボタン */}
        <div
          style={{
            position: "absolute",
            top: "20px",
            left: "20px",
          }}
        >
          <a
            href={`${FRONTEND_URL}/`}
            style={{
              display: "inline-block",
              background: "rgba(255, 255, 255, 0.2)",
              color: "white",
              padding: "8px 15px",
              textDecoration: "none",
              borderRadius: "20px",
              fontWeight: "bold",
              fontSize: "14px",
              transition: "all 0.3s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
            }}
          >
            トップへ戻る
          </a>
        </div>

        {/* 右上のユーザーメニュー */}
        <div
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            display: "flex",
            gap: "10px",
            alignItems: "center",
          }}
        >
          <div
            style={{
              background: "rgba(255, 255, 255, 0.2)",
              padding: "8px 15px",
              borderRadius: "20px",
              fontSize: "14px",
              color: "white",
              fontWeight: "bold",
            }}
          >
            👤 {user.username}
          </div>
          <a
            href={`${BACKEND_URL}/auth?action=logout`}
            style={{
              display: "inline-block",
              background: "rgba(220, 53, 69, 0.8)",
              color: "white",
              padding: "8px 15px",
              textDecoration: "none",
              borderRadius: "20px",
              fontWeight: "bold",
              fontSize: "14px",
              transition: "all 0.3s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(220, 53, 69, 1)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(220, 53, 69, 0.8)";
            }}
          >
            🚪 ログアウト
          </a>
        </div>

        <h1 style={{ margin: 0, fontSize: "2.5rem", fontWeight: "bold" }}>
          シラバス検索
        </h1>
        <p style={{ margin: "10px 0 0 0", fontSize: "1.1rem", opacity: 0.9 }}>
          佐賀大学の講義情報を検索できます
        </p>
      </header>

      <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "20px" }}>
        {/* 検索フィルター */}
        <div
          style={{
            background: "#f8f9fa",
            padding: "25px",
            borderRadius: "10px",
            marginBottom: "30px",
            border: "1px solid #e9ecef",
          }}
        >
          <h2
            style={{
              color: "#1e3c72",
              margin: "0 0 20px 0",
              fontSize: "1.5rem",
            }}
          >
            検索条件
          </h2>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "15px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                  fontWeight: "bold",
                  color: "#333",
                }}
              >
                キーワード検索
              </label>
              <input
                type="text"
                value={filters.keyword}
                onChange={(e) =>
                  setFilters({ ...filters, keyword: e.target.value })
                }
                placeholder="全フィールドで検索"
                style={{
                  width: "100%",
                  padding: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                  fontWeight: "bold",
                  color: "#333",
                }}
              >
                科目コード
              </label>
              <input
                type="text"
                value={filters.code}
                onChange={(e) =>
                  setFilters({ ...filters, code: e.target.value })
                }
                placeholder="例: 50311900"
                style={{
                  width: "100%",
                  padding: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                  fontWeight: "bold",
                  color: "#333",
                }}
              >
                科目名
              </label>
              <input
                type="text"
                value={filters.name}
                onChange={(e) =>
                  setFilters({ ...filters, name: e.target.value })
                }
                placeholder="科目名を入力"
                style={{
                  width: "100%",
                  padding: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                  fontWeight: "bold",
                  color: "#333",
                }}
              >
                担当教員
              </label>
              <input
                type="text"
                value={filters.lecturer}
                onChange={(e) =>
                  setFilters({ ...filters, lecturer: e.target.value })
                }
                placeholder="教員名を入力"
                style={{
                  width: "100%",
                  padding: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                  fontWeight: "bold",
                  color: "#333",
                }}
              >
                学年
              </label>
              <select
                value={filters.grade}
                onChange={(e) =>
                  setFilters({ ...filters, grade: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  fontSize: "14px",
                }}
              >
                <option value="">選択してください</option>
                <option value="1">1年</option>
                <option value="2">2年</option>
                <option value="3">3年</option>
                <option value="4">4年</option>
              </select>
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                  fontWeight: "bold",
                  color: "#333",
                }}
              >
                開講学期
              </label>
              <select
                value={filters.season}
                onChange={(e) =>
                  setFilters({ ...filters, season: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "5px",
                  fontSize: "14px",
                }}
              >
                <option value="">選択してください</option>
                <option value="前期">前期</option>
                <option value="後期">後期</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
            <button
              onClick={handleSearch}
              style={{
                background: "#1e3c72",
                color: "white",
                border: "none",
                padding: "12px 25px",
                borderRadius: "5px",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "bold",
              }}
            >
              検索実行
            </button>
            <button
              onClick={handleReset}
              style={{
                background: "#6c757d",
                color: "white",
                border: "none",
                padding: "12px 25px",
                borderRadius: "5px",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              リセット
            </button>
          </div>
        </div>

        {/* 検索結果 */}
        <div>
          <h2
            style={{
              color: "#1e3c72",
              margin: "0 0 20px 0",
              fontSize: "1.5rem",
            }}
          >
            検索結果 ({lectures.length}件)
          </h2>

          {loading && (
            <div
              style={{
                textAlign: "center",
                padding: "40px",
                fontSize: "1.1rem",
              }}
            >
              検索中...
            </div>
          )}

          {error && (
            <div
              style={{
                background: "#f8d7da",
                color: "#721c24",
                padding: "15px",
                borderRadius: "5px",
                marginBottom: "20px",
              }}
            >
              エラー: {error}
            </div>
          )}

          {!loading && !error && hasSearched && lectures.length === 0 && (
            <div
              style={{
                textAlign: "center",
                padding: "40px",
                color: "#6c757d",
                fontSize: "1.1rem",
              }}
            >
              該当する講義が見つかりませんでした
            </div>
          )}

          {!loading && !error && hasSearched && lectures.length > 0 && (
            <div style={{ display: "grid", gap: "15px" }}>
              {lectures.map((lecture) => (
                <div
                  key={lecture.id}
                  style={{
                    background: "white",
                    border: "1px solid #e9ecef",
                    borderRadius: "8px",
                    padding: "20px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    cursor: "pointer",
                    transition: "box-shadow 0.2s",
                  }}
                  onClick={() =>
                    lecture.code && handleLectureClick(lecture.code)
                  }
                  title="クリックでシラバス詳細を表示"
                >
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr auto",
                      gap: "15px",
                      alignItems: "start",
                    }}
                  >
                    <div>
                      <h3
                        style={{
                          margin: "0 0 10px 0",
                          color: "#1e3c72",
                          fontSize: "1.2rem",
                        }}
                      >
                        {lecture.name || "科目名未設定"}
                      </h3>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "repeat(auto-fit, minmax(200px, 1fr))",
                          gap: "10px",
                          fontSize: "14px",
                        }}
                      >
                        {lecture.code && (
                          <div>
                            <strong>科目コード:</strong> {lecture.code}
                          </div>
                        )}
                        {lecture.lecturer && (
                          <div>
                            <strong>担当教員:</strong> {lecture.lecturer}
                          </div>
                        )}
                        {lecture.grade && (
                          <div>
                            <strong>学年:</strong> {lecture.grade}
                          </div>
                        )}
                        {lecture.season && (
                          <div>
                            <strong>開講学期:</strong> {lecture.season}
                          </div>
                        )}
                        {lecture.time && (
                          <div>
                            <strong>曜日・校時:</strong> {lecture.time}
                          </div>
                        )}
                        {lecture.category && (
                          <div>
                            <strong>カテゴリ:</strong> {lecture.category}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {modalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setModalOpen(false)}
        >
          <div
            style={{
              background: "white",
              borderRadius: "8px",
              padding: "30px",
              maxWidth: "90vw",
              maxHeight: "90vh",
              overflow: "auto",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setModalOpen(false)}
              style={{
                position: "absolute",
                top: 10,
                right: 10,
                background: "#1e3c72",
                color: "white",
                border: "none",
                borderRadius: "50%",
                width: "32px",
                height: "32px",
                fontSize: "18px",
                cursor: "pointer",
              }}
            >
              ×
            </button>
            {modalLoading && <div>読み込み中...</div>}
            {modalError && <div style={{ color: "red" }}>{modalError}</div>}
            {modalHtml && (
              <div
                style={{
                  minWidth: "300px",
                  padding: "10px",
                  background: "#f9f9f9",
                  borderRadius: "8px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                }}
              >
                {/* ここで独自のヘッダーや説明を追加 */}
                <h2 style={{ color: "#1e3c72", marginTop: 0 }}>シラバス詳細</h2>
                <hr style={{ margin: "10px 0 20px 0" }} />
                {/* 取得したHTMLをラップして表示 */}
                <div
                  className="syllabus-html"
                  dangerouslySetInnerHTML={{ __html: modalHtml }}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
