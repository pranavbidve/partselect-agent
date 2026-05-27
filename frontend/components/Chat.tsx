"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ChatInput from "./ChatInput";
import ProductCard from "./ProductCard";
import Cart, { CartItem } from "./Cart";

interface Message {
  role: "user" | "assistant";
  content: string;
  parts?: Part[];
}

interface Part {
  metadata: {
    part_number: string;
    name: string;
    price: number;
    stock_level: number;
    low_stock: boolean;
    image_url: string;
    brand: string;
    category: string;
    compatible_models: string;
  };
  description: string;
}

const SUGGESTED = [
  "The ice maker on my Whirlpool fridge is not working.",
  "How can I install part number PS11752778?",
  "Is PS11752778 compatible with my WDT780SAEM1 dishwasher?",
  "What have I ordered before?",
];

const SESSION_ID = `session-${Math.random().toString(36).slice(2)}`;

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addToCart = (partNumber: string, name: string) => {
    setCartItems((prev) => {
      const existing = prev.find((i) => i.part_number === partNumber);
      if (existing) {
        return prev.map((i) =>
          i.part_number === partNumber ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [...prev, { part_number: partNumber, name, quantity: 1 }];
    });
    sendMessage(`Add ${partNumber} to my cart`);
  };

  const sendMessage = async (text: string) => {
    if (isStreaming) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    setIsStreaming(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: SESSION_ID }),
      });

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const raw = line.slice(5).trim();
          try {
            const event = JSON.parse(raw);
            if (event.type === "token") {
              const text = typeof event.content === "string"
                ? event.content
                : Array.isArray(event.content)
                  ? event.content.filter((b: { type: string }) => b.type === "text").map((b: { text: string }) => b.text).join("")
                  : "";
              if (text) {
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    content: updated[updated.length - 1].content + text,
                  };
                  return updated;
                });
              }
            } else if (event.type === "done") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  parts: event.parts ?? [],
                };
                return updated;
              });
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: "Something went wrong. Please try again.",
        };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="bg-[#0066CC] text-white px-6 py-4 flex items-center justify-between shadow-md flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
            <span className="text-[#0066CC] font-bold text-sm">PS</span>
          </div>
          <div>
            <p className="font-semibold leading-tight">PartSelect Assistant</p>
            <p className="text-xs text-blue-200">Refrigerator & Dishwasher Parts</p>
          </div>
        </div>
        <Cart items={cartItems} />
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div>
              <p className="text-xl font-semibold text-gray-800">How can I help you today?</p>
              <p className="text-sm text-gray-500 mt-1">Find parts, check compatibility, or troubleshoot your appliance.</p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-sm border border-[#0066CC] text-[#0066CC] px-4 py-2 rounded-full hover:bg-blue-50 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] space-y-3`}>
              <div
                className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-[#0066CC] text-white rounded-br-sm whitespace-pre-wrap"
                    : "bg-white text-gray-800 border border-gray-200 rounded-bl-sm shadow-sm prose prose-sm max-w-none prose-headings:text-gray-900 prose-a:text-[#0066CC]"
                }`}
              >
                {msg.role === "assistant" ? (
                  msg.content ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        table: (props) => <table className="w-full text-sm border-collapse my-2" {...props} />,
                        th: (props) => <th className="border border-gray-300 bg-gray-100 px-3 py-1.5 text-left font-semibold" {...props} />,
                        td: (props) => <td className="border border-gray-300 px-3 py-1.5" {...props} />,
                      }}
                    >{msg.content}</ReactMarkdown>
                  ) : isStreaming && i === messages.length - 1 ? (
                    <span className="inline-flex gap-1">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                  ) : null
                ) : (
                  msg.content
                )}
              </div>

              {msg.parts && msg.parts.length > 0 && (
                <div className="space-y-2">
                  {msg.parts.map((part) => (
                    <ProductCard key={part.metadata.part_number} part={part} onAddToCart={addToCart} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white px-4 py-4">
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
    </div>
  );
}
