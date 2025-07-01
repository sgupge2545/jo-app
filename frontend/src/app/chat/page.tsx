"use client";

import { useState, useEffect, useRef } from "react";

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface PageData {
  title: string;
  html_content: string;
  css_content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageData | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自動スクロール
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  // チャットメッセージを送信
  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      // チャットAPIを呼び出し
      const chatResponse = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: inputText }),
      });

      const chatData = await chatResponse.json();

      // AIのレスポンスを追加
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: chatData.response,
        isUser: false,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);

      // ページ生成を試行
      try {
        const pageResponse = await fetch("/api/generate-page", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ prompt: inputText }),
        });

        const pageData = await pageResponse.json();
        setCurrentPage(pageData);
        applyCSS(pageData.css_content);

        // ページ生成完了のメッセージを追加
        const pageMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          text: "ページを生成しました！下のプレビューで確認できます。",
          isUser: false,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, pageMessage]);
      } catch (pageError) {
        console.error("ページ生成エラー:", pageError);
      }
    } catch (error) {
      console.error("チャットエラー:", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: "エラーが発生しました。もう一度お試しください。",
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Enterキーで送信
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>AIページ生成チャット</h1>
        <p>AIとチャットして、美しいWebページを作成しましょう</p>
      </div>

      <div className="chat-layout">
        {/* チャットエリア */}
        <div className="chat-area">
          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <h3>ようこそ！</h3>
                <p>どのようなページを作成したいですか？</p>
                <div className="suggestions">
                  <button
                    onClick={() =>
                      setInputText(
                        "モダンなランディングページを作成してください"
                      )
                    }
                  >
                    モダンなランディングページ
                  </button>
                  <button
                    onClick={() =>
                      setInputText(
                        "ダークテーマのポートフォリオページを作成してください"
                      )
                    }
                  >
                    ダークテーマのポートフォリオ
                  </button>
                  <button
                    onClick={() =>
                      setInputText("ミニマルなブログページを作成してください")
                    }
                  >
                    ミニマルなブログページ
                  </button>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.isUser ? "user" : "ai"}`}
              >
                <div className="message-content">
                  <p>{message.text}</p>
                  <span className="timestamp">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message ai">
                <div className="message-content">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="どのようなページを作成したいですか？"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputText.trim() || isLoading}
              className="send-button"
            >
              送信
            </button>
          </div>
        </div>

        {/* プレビューエリア */}
        <div className="preview-area">
          <h3>ページプレビュー</h3>
          {currentPage ? (
            <div className="preview-content">
              <div
                dangerouslySetInnerHTML={{ __html: currentPage.html_content }}
              />
            </div>
          ) : (
            <div className="preview-placeholder">
              <p>
                チャットでページを生成すると、ここにプレビューが表示されます
              </p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .chat-container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 20px;
          height: 100vh;
          display: flex;
          flex-direction: column;
        }

        .chat-header {
          text-align: center;
          margin-bottom: 20px;
        }

        .chat-header h1 {
          color: #333;
          margin-bottom: 10px;
        }

        .chat-header p {
          color: #666;
        }

        .chat-layout {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          flex: 1;
          min-height: 0;
        }

        .chat-area {
          display: flex;
          flex-direction: column;
          border: 1px solid #e0e0e0;
          border-radius: 10px;
          background: white;
        }

        .messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .welcome-message {
          text-align: center;
          padding: 40px 20px;
        }

        .welcome-message h3 {
          color: #333;
          margin-bottom: 10px;
        }

        .suggestions {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-top: 20px;
        }

        .suggestions button {
          padding: 10px 15px;
          border: 1px solid #007bff;
          background: white;
          color: #007bff;
          border-radius: 5px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .suggestions button:hover {
          background: #007bff;
          color: white;
        }

        .message {
          margin-bottom: 15px;
          display: flex;
        }

        .message.user {
          justify-content: flex-end;
        }

        .message-content {
          max-width: 70%;
          padding: 12px 16px;
          border-radius: 15px;
          position: relative;
        }

        .message.user .message-content {
          background: #007bff;
          color: white;
          border-bottom-right-radius: 5px;
        }

        .message.ai .message-content {
          background: #f1f3f4;
          color: #333;
          border-bottom-left-radius: 5px;
        }

        .timestamp {
          font-size: 0.7rem;
          opacity: 0.7;
          margin-top: 5px;
          display: block;
        }

        .loading-dots {
          display: flex;
          gap: 4px;
        }

        .loading-dots span {
          width: 8px;
          height: 8px;
          background: #666;
          border-radius: 50%;
          animation: bounce 1.4s infinite ease-in-out;
        }

        .loading-dots span:nth-child(1) {
          animation-delay: -0.32s;
        }
        .loading-dots span:nth-child(2) {
          animation-delay: -0.16s;
        }

        @keyframes bounce {
          0%,
          80%,
          100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }

        .input-area {
          display: flex;
          padding: 20px;
          border-top: 1px solid #e0e0e0;
          gap: 10px;
        }

        .input-area textarea {
          flex: 1;
          padding: 12px;
          border: 1px solid #ddd;
          border-radius: 8px;
          resize: none;
          height: 50px;
          font-family: inherit;
        }

        .send-button {
          padding: 12px 24px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.3s ease;
        }

        .send-button:hover:not(:disabled) {
          background: #0056b3;
        }

        .send-button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .preview-area {
          border: 1px solid #e0e0e0;
          border-radius: 10px;
          background: white;
          display: flex;
          flex-direction: column;
        }

        .preview-area h3 {
          padding: 20px;
          margin: 0;
          border-bottom: 1px solid #e0e0e0;
          color: #333;
        }

        .preview-content {
          flex: 1;
          overflow-y: auto;
          padding: 0;
        }

        .preview-placeholder {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666;
          text-align: center;
          padding: 40px;
        }

        @media (max-width: 768px) {
          .chat-layout {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
