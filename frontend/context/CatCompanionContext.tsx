"use client";

import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";
import {
  CatState,
  CompanionChatMessage,
  CompanionChatRequest,
  CompanionContextData,
} from "@/types";
import { api } from "@/lib/api";

interface CatCompanionContextType {
  catState: CatState;
  setCatState: (state: CatState) => void;
  mode: "study" | "general";
  setMode: (mode: "study" | "general") => void;
  isChatOpen: boolean;
  openChat: (initialPrompt?: string, forceMode?: "study" | "general") => void;
  closeChat: () => void;
  toggleChat: () => void;
  speechBubble: string | null;
  triggerSpeechBubble: (message: string, durationMs?: number, state?: CatState) => void;
  dismissSpeechBubble: () => void;
  companionContext: CompanionContextData;
  setCompanionContext: (ctx: Partial<CompanionContextData>) => void;
  isMinimized: boolean;
  setIsMinimized: (val: boolean) => void;
  isMuted: boolean;
  setIsMuted: (val: boolean) => void;
  messages: CompanionChatMessage[];
  sendMessage: (text: string, customMode?: "study" | "general") => Promise<void>;
  isThinking: boolean;
  clearChat: () => void;
}

const CatCompanionContext = createContext<CatCompanionContextType | undefined>(undefined);

export function CatCompanionProvider({ children }: { children: React.ReactNode }) {
  const [catState, setCatStateInternal] = useState<CatState>("IDLE");
  const [mode, setMode] = useState<"study" | "general">("study");
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [speechBubble, setSpeechBubble] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [companionContext, setCompanionContextState] = useState<CompanionContextData>({
    pageType: "dashboard",
  });

  const [messages, setMessages] = useState<CompanionChatMessage[]>([
    {
      id: "welcome-1",
      role: "assistant",
      content:
        "Greetings, brave scholar! 🐱⚔️ I am **Sir Paws-a-Lot**, your AI study knight companion. I'm here to help you conquer your syllabus notes, clarify tricky concepts, and guide you through your quiz quests! How can I assist you right now?",
      mode: "study",
      catState: "EXPLAINING",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      quickActions: ["Explain simply", "Summarize topic", "Give me a hint", "Quiz me"],
    },
  ]);

  const speechTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastInteractionTimeRef = useRef<number>(Date.now());

  const setCatState = useCallback((state: CatState) => {
    setCatStateInternal(state);
  }, []);

  const setCompanionContext = useCallback((ctx: Partial<CompanionContextData>) => {
    setCompanionContextState((prev) => ({ ...prev, ...ctx }));
  }, []);

  const triggerSpeechBubble = useCallback(
    (message: string, durationMs: number = 7000, state?: CatState) => {
      if (isMuted) return;
      if (speechTimeoutRef.current) clearTimeout(speechTimeoutRef.current);
      setSpeechBubble(message);
      if (state) setCatState(state);

      speechTimeoutRef.current = setTimeout(() => {
        setSpeechBubble(null);
      }, durationMs);
    },
    [isMuted, setCatState]
  );

  const dismissSpeechBubble = useCallback(() => {
    if (speechTimeoutRef.current) clearTimeout(speechTimeoutRef.current);
    setSpeechBubble(null);
  }, []);

  const openChat = useCallback(
    (initialPrompt?: string, forceMode?: "study" | "general") => {
      setIsChatOpen(true);
      setIsMinimized(false);
      dismissSpeechBubble();
      if (forceMode) setMode(forceMode);
      setCatState("EXPLAINING");

      if (initialPrompt) {
        // Send initial prompt shortly after opening
        setTimeout(() => {
          sendMessage(initialPrompt, forceMode);
        }, 150);
      }
    },
    [dismissSpeechBubble, setCatState]
  );

  const closeChat = useCallback(() => {
    setIsChatOpen(false);
    setCatState("IDLE");
  }, [setCatState]);

  const toggleChat = useCallback(() => {
    if (isChatOpen) {
      closeChat();
    } else {
      openChat();
    }
  }, [isChatOpen, closeChat, openChat]);

  const clearChat = useCallback(() => {
    setMessages([
      {
        id: "fresh-" + Date.now(),
        role: "assistant",
        content: "Refreshed and ready for our next mission! 🐱⚔️ What would you like to study?",
        mode: mode,
        catState: "IDLE",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        quickActions: ["Explain simply", "Summarize topic", "Give me a hint"],
      },
    ]);
  }, [mode]);

  // Send message to companion backend
  const sendMessage = async (text: string, customMode?: "study" | "general") => {
    if (!text.trim() || isThinking) return;

    const activeMode = customMode || mode;
    const userMsg: CompanionChatMessage = {
      id: "u-" + Date.now(),
      role: "user",
      content: text,
      mode: activeMode,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);
    setCatState("THINKING");

    try {
      const historyPayload = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const req: CompanionChatRequest = {
        message: text,
        mode: activeMode,
        topic_id: companionContext.topicId || null,
        topic_name: companionContext.topicName || null,
        unit_id: companionContext.unitId || null,
        unit_name: companionContext.unitTitle || null,
        subject_id: companionContext.subjectId || null,
        subject_name: companionContext.subjectName || null,
        current_page: companionContext.pageType || null,
        current_question: companionContext.currentQuestion || null,
        history: historyPayload,
      };

      const res = await api.chatWithCompanion(req);

      const botMsg: CompanionChatMessage = {
        id: "a-" + Date.now(),
        role: "assistant",
        content: res.response,
        mode: res.mode,
        catState: res.cat_state,
        sourceReference: res.source_reference,
        requiresGeneralPrompt: res.requires_general_prompt,
        outsideConcept: res.outside_concept,
        quickActions: res.quick_actions,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
      setCatState(res.cat_state || "EXPLAINING");

      if (res.speech_bubble && !isMuted) {
        triggerSpeechBubble(res.speech_bubble, 6000, res.cat_state);
      }
    } catch (err: any) {
      const errorMsg: CompanionChatMessage = {
        id: "err-" + Date.now(),
        role: "assistant",
        content:
          "My whiskers sense a temporary interference in our magical communications! Please try again in a moment. 🐾",
        mode: activeMode,
        catState: "SUPPORTIVE",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setCatState("SUPPORTIVE");
    } finally {
      setIsThinking(false);
    }
  };

  // Inactivity tracking for SLEEPY state (75s inactivity)
  useEffect(() => {
    const handleActivity = () => {
      lastInteractionTimeRef.current = Date.now();
      if (catState === "SLEEPY") {
        setCatState("IDLE");
        triggerSpeechBubble("I'm awake and ready to study! 🐱⚔️", 4000);
      }
    };

    window.addEventListener("mousemove", handleActivity);
    window.addEventListener("keydown", handleActivity);
    window.addEventListener("click", handleActivity);
    window.addEventListener("scroll", handleActivity);

    inactivityTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - lastInteractionTimeRef.current;
      if (elapsed > 75000 && catState === "IDLE" && !isChatOpen) {
        setCatState("SLEEPY");
        triggerSpeechBubble("Zzz... taking a tiny knight nap! Wake me anytime. 😴", 5000, "SLEEPY");
      }
    }, 15000);

    return () => {
      window.removeEventListener("mousemove", handleActivity);
      window.removeEventListener("keydown", handleActivity);
      window.removeEventListener("click", handleActivity);
      window.removeEventListener("scroll", handleActivity);
      if (inactivityTimerRef.current) clearInterval(inactivityTimerRef.current);
      if (speechTimeoutRef.current) clearTimeout(speechTimeoutRef.current);
    };
  }, [catState, isChatOpen, triggerSpeechBubble, setCatState]);

  return (
    <CatCompanionContext.Provider
      value={{
        catState,
        setCatState,
        mode,
        setMode,
        isChatOpen,
        openChat,
        closeChat,
        toggleChat,
        speechBubble,
        triggerSpeechBubble,
        dismissSpeechBubble,
        companionContext,
        setCompanionContext,
        isMinimized,
        setIsMinimized,
        isMuted,
        setIsMuted,
        messages,
        sendMessage,
        isThinking,
        clearChat,
      }}
    >
      {children}
    </CatCompanionContext.Provider>
  );
}

export function useCatCompanion() {
  const context = useContext(CatCompanionContext);
  if (!context) {
    throw new Error("useCatCompanion must be used within a CatCompanionProvider");
  }
  return context;
}
