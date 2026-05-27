"use client";

import { useRef } from "react";

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  const send = () => {
    const value = ref.current?.value.trim();
    if (!value || disabled) return;
    onSend(value);
    if (ref.current) ref.current.value = "";
  };

  return (
    <div className="flex gap-2 items-end">
      <textarea
        ref={ref}
        rows={1}
        disabled={disabled}
        placeholder="Ask about parts, compatibility, or troubleshooting..."
        className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent disabled:opacity-50 bg-white"
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
          }
        }}
      />
      <button
        onClick={send}
        disabled={disabled}
        className="bg-[#0066CC] text-white px-5 py-3 rounded-xl hover:bg-[#0052a3] disabled:opacity-50 transition-colors font-medium text-sm whitespace-nowrap"
      >
        {disabled ? "..." : "Send"}
      </button>
    </div>
  );
}
