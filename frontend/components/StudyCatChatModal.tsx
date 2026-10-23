"use client";

import React, { useState, useRef, useEffect } from "react";
import { useCatCompanion } from "@/context/CatCompanionContext";
import StudyCatAvatar from "@/components/StudyCatAvatar";
import {
  X,
  Send,
  Sparkles,
  BookOpen,
  Globe,
  RotateCcw,
  HelpCircle,
  Minimize2,
  ChevronRight,
  ShieldCheck,
  Brain,
  Lightbulb,
} from "lucide-react";

export default function StudyCatChatModal() {
  const {
    isChatOpen,
    closeChat,
    catState,
    mode,
    setMode,
    messages,
    sendMessage,
    isThinking,
    companionContext,
    clearChat,
  } = useCatCompanion();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    if (isChatOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isThinking, isChatOpen]);

  // Focus input on open
  useEffect(() => {
    if (isChatOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isChatOpen]);

  if (!isChatOpen) return null;

  const handleSend = async () => {
    if (!input.trim() || isThinking) return;
    const text = input;
    setInput("");
    await sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = async (actionText: string) => {
    if (actionText === "Explain Generally") {
      setMode("general");
      await sendMessage("Please give me a general explanation of this concept.", "general");
    } else if (actionText === "Switch back to Study Mode") {
      setMode("study");
      await sendMessage("Let's return to our syllabus study notes.", "study");
    } else {
      await sendMessage(actionText);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="AI Study Cat Companion Chat"
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:justify-end p-0 sm:p-6 bg-black/40 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
    >
      <div className="relative w-full sm:w-[480px] h-[92vh] sm:h-[680px] max-h-full bg-white sm:rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 p-4 text-white flex flex-col gap-2.5 shadow-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StudyCatAvatar state={catState} size="sm" showBadge={false} />
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-extrabold text-sm sm:text-base tracking-tight text-white flex items-center gap-1.5">
                    <span>Sir Paws-a-Lot</span>
                    <span className="text-xs font-normal text-cyan-300">⚔️ AI Knight</span>
                  </h3>
                </div>
                <p className="text-[11px] text-indigo-200 flex items-center gap-1">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span>Your AI Study Companion</span>
                  {companionContext.topicName && (
                    <span className="truncate max-w-[160px] text-indigo-300">
                      • {companionContext.topicName}
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={clearChat}
                title="Restart Chat"
                className="p-1.5 text-indigo-300 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
              <button
                onClick={closeChat}
                title="Close Companion"
                className="p-1.5 text-indigo-300 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Active Context Lens Banner */}
          <div className="flex items-center justify-between bg-black/30 rounded-xl px-3 py-1.5 border border-white/10 text-xs">
            <div className="flex items-center gap-1.5 text-indigo-200 truncate">
              <BookOpen className="h-3.5 w-3.5 text-cyan-300 shrink-0" />
              <span className="font-semibold text-white">Context:</span>
              <span className="truncate text-cyan-200">
                {companionContext.subjectName || "Coursework"}
                {companionContext.topicName ? ` → ${companionContext.topicName}` : ""}
              </span>
            </div>
            <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full font-medium shrink-0 border border-emerald-400/30">
              Active Context
            </span>
          </div>
        </div>

        {/* Messages Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/70">
          {messages.map((m) => {
            const isUser = m.role === "user";
            return (
              <div
                key={m.id}
                className={`flex gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="shrink-0 mt-1">
                    <StudyCatAvatar state={m.catState || "EXPLAINING"} size="sm" showBadge={false} />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-3.5 text-xs sm:text-sm leading-relaxed shadow-2xs ${
                    isUser
                      ? "bg-indigo-600 text-white rounded-br-xs"
                      : "bg-white text-gray-800 border border-gray-200 rounded-tl-xs"
                  }`}
                >
                  {/* Message Content */}
                  <div className="whitespace-pre-wrap font-sans">{m.content}</div>

                  {/* Optional Subtle Course Reference Citation */}
                  {m.sourceReference && (
                    <div className="mt-2.5 pt-2 border-t border-gray-100 text-[11px] text-indigo-700 flex items-start gap-1.5 bg-indigo-50/60 p-2 rounded-lg">
                      <BookOpen className="h-3.5 w-3.5 text-indigo-600 shrink-0 mt-0.5" />
                      <span className="font-medium">📚 Related course material: {m.sourceReference}</span>
                    </div>
                  )}

                  {/* Contextual Quick Actions rendered inside bot message */}
                  {!isUser && m.quickActions && m.quickActions.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-100 flex flex-wrap gap-1.5">
                      {m.quickActions.map((action, aIdx) => (
                        <button
                          key={aIdx}
                          onClick={() => handleQuickAction(action)}
                          className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-all ${
                            action.includes("Generally")
                              ? "bg-teal-100 text-teal-800 border border-teal-300 hover:bg-teal-200"
                              : "bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100"
                          }`}
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="mt-1.5 text-[9px] text-gray-400 text-right">
                    {m.timestamp}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Thinking State */}
          {isThinking && (
            <div className="flex gap-2.5 justify-start items-center">
              <StudyCatAvatar state="THINKING" size="sm" showBadge={false} />
              <div className="bg-white border border-cyan-200 rounded-2xl rounded-tl-xs p-3 text-xs text-gray-700 flex items-center gap-2 shadow-sm">
                <span className="flex h-2 w-2 rounded-full bg-cyan-500 animate-ping" />
                <span className="font-medium text-cyan-900">
                  Sir Paws-a-Lot is consulting your scrolls... 🐾
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Context Quick Action Chips Toolbar */}
        <div className="px-3 pt-2 pb-1 bg-white border-t border-gray-100 flex items-center gap-1.5 overflow-x-auto text-xs no-scrollbar">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider shrink-0">
            Quick Quests:
          </span>
          <button
            onClick={() => handleQuickAction("Explain simply")}
            className="shrink-0 rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 px-2.5 py-1 text-[11px] font-medium text-gray-700 border border-gray-200"
          >
            Explain simply
          </button>
          <button
            onClick={() => handleQuickAction("What does this mean?")}
            className="shrink-0 rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 px-2.5 py-1 text-[11px] font-medium text-gray-700 border border-gray-200"
          >
            What does this mean?
          </button>
          <button
            onClick={() => handleQuickAction("Give an example")}
            className="shrink-0 rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 px-2.5 py-1 text-[11px] font-medium text-gray-700 border border-gray-200"
          >
            Give an example
          </button>
          <button
            onClick={() => handleQuickAction("Give me a hint")}
            className="shrink-0 rounded-full bg-slate-100 hover:bg-amber-50 hover:text-amber-800 px-2.5 py-1 text-[11px] font-medium text-gray-700 border border-gray-200"
          >
            Give a hint 💡
          </button>
        </div>

        {/* Input Bar */}
        <div className="p-3 bg-white border-t border-gray-200">
          <div className="relative flex items-center">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                companionContext.topicName
                  ? `Ask Sir Paws-a-Lot about ${companionContext.topicName} or any concept...`
                  : "Ask Sir Paws-a-Lot anything..."
              }
              className="w-full rounded-2xl border border-gray-300 py-2.5 pl-4 pr-12 text-xs sm:text-sm focus:border-indigo-600 focus:outline-hidden focus:ring-1 focus:ring-indigo-600"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isThinking}
              className="absolute right-1.5 p-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>

          <p className="mt-1.5 text-[10px] text-gray-400 text-center flex items-center justify-center gap-1">
            <ShieldCheck className="h-3 w-3 text-emerald-500" />
            <span>
              {companionContext.topicName
                ? `Informed by your ${companionContext.topicName} notes. Real-world examples and explanations welcome!`
                : "Your intelligent study companion. Ask about course concepts, definitions, or examples."}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
