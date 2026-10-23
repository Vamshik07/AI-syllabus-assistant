"use client";

import React, { useState } from "react";
import { useCatCompanion } from "@/context/CatCompanionContext";
import StudyCatAvatar from "@/components/StudyCatAvatar";
import StudyCatChatModal from "@/components/StudyCatChatModal";
import { MessageSquare, X, Minus, Sparkles, Sword } from "lucide-react";

export default function StudyCatCompanion() {
  const {
    catState,
    speechBubble,
    dismissSpeechBubble,
    openChat,
    isChatOpen,
    isMinimized,
    setIsMinimized,
    companionContext,
  } = useCatCompanion();

  // If chat is open, we show the modal (the companion can still be visible or docked)
  if (isMinimized) {
    return (
      <>
        {/* Minimized Cute Paw Pill */}
        <div className="fixed bottom-4 right-4 z-40 select-none">
          <button
            onClick={() => setIsMinimized(false)}
            title="Expand Sir Paws-a-Lot (AI Study Cat)"
            className="group flex items-center gap-2 rounded-full bg-indigo-900/90 text-white px-3 py-1.5 shadow-lg border border-cyan-400/50 hover:bg-indigo-800 transition-all hover:scale-105"
          >
            <div className="w-6 h-6 rounded-full overflow-hidden border border-cyan-400">
              <StudyCatAvatar state={catState} size="sm" showBadge={false} />
            </div>
            <span className="text-xs font-bold text-cyan-200 group-hover:text-white">
              Sir Paws-a-Lot
            </span>
            <span className="text-[10px] text-emerald-400 font-mono">●</span>
          </button>
        </div>
        <StudyCatChatModal />
      </>
    );
  }

  return (
    <>
      {/* Floating Study Cat Companion Container */}
      <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end pointer-events-none select-none">
        {/* Contextual Speech Bubble */}
        {speechBubble && !isChatOpen && (
          <div className="pointer-events-auto mb-2 max-w-xs sm:max-w-sm rounded-2xl bg-white/95 p-3.5 shadow-xl border border-indigo-200 text-xs text-gray-800 backdrop-blur-xs relative animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* Speech bubble pointer triangle */}
            <div className="absolute -bottom-2 right-8 h-4 w-4 rotate-45 bg-white border-r border-b border-indigo-200" />

            <div className="flex items-start justify-between gap-2">
              <div
                onClick={() => openChat()}
                className="cursor-pointer hover:text-indigo-600 transition-colors"
              >
                <div className="flex items-center gap-1.5 font-bold text-indigo-700 text-[11px] mb-1">
                  <Sparkles className="h-3 w-3 text-cyan-500" />
                  <span>Sir Paws-a-Lot:</span>
                </div>
                <p className="leading-snug">{speechBubble}</p>
                <span className="mt-1.5 inline-block text-[10px] font-semibold text-indigo-500 hover:underline">
                  Tap to chat with me →
                </span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  dismissSpeechBubble();
                }}
                title="Dismiss message"
                className="text-gray-400 hover:text-gray-600 p-0.5 rounded-md"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Character Avatar & Quick Control Group */}
        <div className="pointer-events-auto relative group flex items-center justify-end">
          {/* Quick minimize control on hover */}
          <button
            onClick={() => setIsMinimized(true)}
            title="Minimize companion"
            aria-label="Minimize AI study cat companion"
            className="absolute -top-2 left-0 z-30 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 text-white p-1 rounded-full shadow-md hover:bg-slate-700"
          >
            <Minus className="h-3 w-3" />
          </button>

          {/* Interactive Cat Avatar */}
          <div
            onClick={() => openChat()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                openChat();
              }
            }}
            aria-label="Open AI Study Cat Companion Chat with Sir Paws-a-Lot"
            title="Sir Paws-a-Lot: Click to ask anything or get study hints!"
            className="cursor-pointer transition-transform duration-200 hover:scale-105 active:scale-95 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full"
          >
            <StudyCatAvatar state={catState} size="md" isInteractive showBadge />
          </div>
        </div>
      </div>

      {/* Expandable Chat Modal */}
      <StudyCatChatModal />
    </>
  );
}
