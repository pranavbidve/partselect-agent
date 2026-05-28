import React, { useState, useRef, useEffect } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import ProductCard from "./ProductCard";
import Cart from "./Cart";
import { marked } from "marked";

const SUGGESTED = [
  "The ice maker on my Whirlpool fridge is not working.",
  "How can I install part number PS11752778?",
  "Is PS11752778 compatible with my WDT780SAEM1 dishwasher?",
  "What have I ordered before?",
];

const SESSION_ID = `session-${Math.random().toString(36).slice(2)}`;

function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addToCart = (partNumber, name) => {
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

  const sendMessage = async (text) => {
    if (isStreaming || !text.trim()) return;
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]);
    setIsStreaming(true);

    try {
      await getAIMessage(
        text,
        SESSION_ID,
        (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: updated[updated.length - 1].content + token,
            };
            return updated;
          });
        },
        (parts) => {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              parts: parts ?? [],
            };
            return updated;
          });
        }
      );
    } catch {
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

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div>
      <div className="cart-overlay">
        <Cart items={cartItems} />
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome">
            <p className="welcome-title">How can I help you today?</p>
            <div className="suggested-prompts">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  className="suggested-btn"
                  onClick={() => sendMessage(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={
              msg.role === "user"
                ? "user-message-container"
                : "assistant-message-container"
            }
          >
            {msg.role === "user" ? (
              <div className="message user-message">{msg.content}</div>
            ) : msg.content ? (
              <div
                className="message assistant-message"
                dangerouslySetInnerHTML={{ __html: marked(msg.content) }}
              />
            ) : isStreaming && i === messages.length - 1 ? (
              <div className="message assistant-message">
                <span className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </span>
              </div>
            ) : null}

            {msg.parts && msg.parts.length > 0 && (
              <div className="parts-list">
                {msg.parts.map((part) => (
                  <ProductCard
                    key={part.metadata.part_number}
                    part={part}
                    onAddToCart={addToCart}
                  />
                ))}
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about parts, compatibility, or troubleshooting..."
          disabled={isStreaming}
        />
        <button onClick={() => sendMessage(input)} disabled={isStreaming}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;
