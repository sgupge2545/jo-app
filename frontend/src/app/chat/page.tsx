"use client";
import { useEffect, useRef, useState } from "react";
import type React from "react";
import Image from "next/image";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, User, ArrowLeft } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ChatBot() {
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string }[]
  >([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;
    const userMsg = { role: "user" as const, content: input };
    const currentInput = input;
    setMessages((msgs) => [...msgs, userMsg]);
    setIsLoading(true);
    setInput("");
    let aiContent = "";
    let assistantMessageIndex = -1;

    try {
      // SSE用のFormDataを作成
      const response = await fetch("/~s23238268/chat-sse-proxy.php", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentInput }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6); // "data: " を除去
              if (data === "[DONE]") {
                done = true;
                break;
              }
              if (data.trim()) {
                aiContent += data;
                setMessages((msgs) => {
                  const newMsgs = [...msgs];
                  if (assistantMessageIndex === -1) {
                    newMsgs.push({ role: "assistant", content: aiContent });
                    assistantMessageIndex = newMsgs.length - 1;
                    setIsLoading(false);
                  } else {
                    newMsgs[assistantMessageIndex] = {
                      role: "assistant",
                      content: aiContent,
                    };
                  }
                  return newMsgs;
                });
              }
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages((msgs) => {
        const newMsgs = [...msgs];
        if (assistantMessageIndex === -1) {
          newMsgs.push({
            role: "assistant",
            content: "[エラーが発生しました]",
          });
        } else {
          newMsgs[assistantMessageIndex] = {
            role: "assistant",
            content: "[エラーが発生しました]",
          };
        }
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (isLoading) return;
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="h-screen flex flex-col max-w-4xl mx-auto">
      {/* Header */}
      <div className="p-4 border-b bg-white">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              (window.location.href =
                "https://stuext.ai.is.saga-u.ac.jp/~s23238268/")
            }
            className="p-2 hover:bg-gray-100 mr-auto"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
            <span className="text-sm font-medium">トップページに戻る</span>
          </Button>
          <Image
            src="/katti.png"
            alt="カッチーくん"
            width={120}
            height={120}
            className="rounded-full object-cover"
          />
          <div>
            <h1 className="text-xl font-semibold text-gray-800">
              カッチーくんに聞く
            </h1>
            <p className="text-sm text-gray-600">何でもお気軽に聞いてカチ！</p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div
        className="flex-1 overflow-auto p-4"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Image
                src="/~s23238268/saga-u.png"
                alt="佐賀大学"
                width={200}
                height={200}
                className="mx-auto mb-4 object-contain opacity-40"
              />
              <p className="text-gray-600 text-lg font-medium">こんにちは！</p>
              <p className="text-gray-500">講義に関するご質問はありますか？</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <Image
                  src="/~s23238268/katti.png"
                  alt="カッチーくん"
                  width={40}
                  height={40}
                  className="rounded-full object-contain flex-shrink-0 w-10 h-10"
                />
              )}

              <div
                className={`max-w-[calc(100%-120px)] ${
                  msg.role === "user" ? "order-first" : ""
                }`}
              >
                <Card className="shadow-none border-0 bg-gray-50">
                  <CardContent className="">
                    <div className="whitespace-pre-wrap break-words text-sm">
                      <ReactMarkdown
                        components={{
                          a: (props) => (
                            <a
                              className="text-blue-600 hover:underline"
                              target="_blank"
                              rel="noopener noreferrer"
                              {...props}
                            />
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {msg.role === "user" && (
                <Avatar className="w-8 h-8 bg-blue-600 flex-shrink-0 border-2 border-blue-700 shadow-lg">
                  <AvatarFallback>
                    <User className="w-4 h-4 text-white" />
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <Image
                src="/~s23238268/katti.png"
                alt="カッチーくん"
                width={40}
                height={40}
                className="rounded-full object-contain flex-shrink-0 w-10 h-10"
              />
              <div className="max-w-[calc(100%-120px)]">
                <Card className="shadow-none border-0 bg-gray-50">
                  <CardContent className="">
                    <div
                      className="flex items-center justify-center space-x-1"
                      aria-label="読み込み中"
                    >
                      <div
                        className="w-1.5 h-1.5 bg-gray-600 rounded-full animate-bounce"
                        style={{ animationDelay: "0s" }}
                      ></div>
                      <div
                        className="w-1.5 h-1.5 bg-gray-600 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                      <div
                        className="w-1.5 h-1.5 bg-gray-600 rounded-full animate-bounce"
                        style={{ animationDelay: "0.4s" }}
                      ></div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-white">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <Input
              placeholder="メッセージを送信する"
              value={input}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="pr-12 min-h-[44px]"
              style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
            />
            <Button
              size="sm"
              disabled={isLoading || !input.trim()}
              onClick={() => !isLoading && handleSubmit()}
              className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
