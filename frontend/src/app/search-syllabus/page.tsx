"use client";

import { useState } from "react";

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

export default function SearchSyllabus() {
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

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
        `/~s23238268/search-syllabus-proxy.php?${params.toString()}`
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
        }}
      >
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
                  }}
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
    </div>
  );
}
