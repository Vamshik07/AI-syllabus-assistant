"use client";

import React from "react";
import Image from "next/image";
import { CatState } from "@/types";
import { Sparkles, Brain, BookOpen, Sword, Lightbulb, Trophy, Moon, Globe, Heart } from "lucide-react";

interface StudyCatAvatarProps {
  state: CatState;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  showBadge?: boolean;
  isInteractive?: boolean;
}

export default function StudyCatAvatar({
  state,
  size = "md",
  className = "",
  showBadge = true,
  isInteractive = false,
}: StudyCatAvatarProps) {
  // Map CatState to the consistent generated character asset
  const getImageSource = (s: CatState): string => {
    switch (s) {
      case "SLEEPY":
        return "/assets/ai-cat/study_cat_sleepy.jpg";
      case "CELEBRATION":
      case "SUCCESS":
      case "HAPPY":
        return "/assets/ai-cat/study_cat_celebration.jpg";
      case "THINKING":
      case "CURIOUS":
      case "HINT":
      case "GENERAL_KNOWLEDGE":
        return "/assets/ai-cat/study_cat_thinking.jpg";
      case "EXPLAINING":
      case "STUDYING":
      case "QUIZ":
      case "ROADMAP":
      case "STUDY_MODE":
      case "SUPPORTIVE":
      case "IDLE":
      default:
        return "/assets/ai-cat/study_cat_idle.jpg";
    }
  };

  // State-specific badges and icons
  const getStateBadge = (s: CatState) => {
    switch (s) {
      case "THINKING":
        return { label: "Thinking...", icon: Brain, color: "bg-cyan-500 text-white animate-pulse" };
      case "HINT":
        return { label: "Hint Ready", icon: Lightbulb, color: "bg-amber-500 text-white" };
      case "QUIZ":
        return { label: "Quiz Quest", icon: Sword, color: "bg-indigo-600 text-white" };
      case "STUDYING":
        return { label: "Studying", icon: BookOpen, color: "bg-blue-600 text-white" };
      case "SUCCESS":
      case "HAPPY":
        return { label: "Victory!", icon: Sparkles, color: "bg-emerald-500 text-white" };
      case "CELEBRATION":
        return { label: "Celebration!", icon: Trophy, color: "bg-purple-600 text-white animate-bounce" };
      case "SLEEPY":
        return { label: "Sleeping Zzz", icon: Moon, color: "bg-slate-600 text-white" };
      case "GENERAL_KNOWLEDGE":
        return { label: "General Mode", icon: Globe, color: "bg-teal-600 text-white" };
      case "SUPPORTIVE":
        return { label: "Here with you", icon: Heart, color: "bg-rose-500 text-white" };
      case "EXPLAINING":
        return { label: "Explaining", icon: Sparkles, color: "bg-indigo-500 text-white" };
      default:
        return { label: "Study Companion", icon: Sword, color: "bg-indigo-600 text-white" };
    }
  };

  const badge = getStateBadge(state);
  const BadgeIcon = badge.icon;

  const sizeClasses = {
    sm: "w-12 h-12",
    md: "w-20 h-20",
    lg: "w-28 h-28",
    xl: "w-40 h-40",
  }[size];

  const imageSizes = {
    sm: 48,
    md: 80,
    lg: 112,
    xl: 160,
  }[size];

  // Animation classes per state (gracefully respects prefers-reduced-motion via Tailwind)
  const getMotionClass = (s: CatState): string => {
    switch (s) {
      case "SUCCESS":
      case "HAPPY":
        return "motion-safe:animate-bounce";
      case "CELEBRATION":
        return "motion-safe:animate-bounce shadow-purple-400/60";
      case "THINKING":
        return "motion-safe:animate-pulse";
      case "SLEEPY":
        return "opacity-90";
      case "IDLE":
      default:
        return "motion-safe:animate-float";
    }
  };

  return (
    <div className={`relative inline-flex items-center justify-center select-none ${className}`}>
      {/* Floating Sparkle / Magic AI Orb */}
      {state !== "SLEEPY" && size !== "sm" && (
        <div
          className="absolute -top-1 -right-1 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-cyan-400/90 text-cyan-950 shadow-md shadow-cyan-300/80 motion-safe:animate-ping opacity-75 pointer-events-none"
          title="Magic AI Companion Orb"
        />
      )}

      {/* Floating Zzz on Sleepy State */}
      {state === "SLEEPY" && (
        <div className="absolute -top-3 -right-2 z-20 flex flex-col items-center pointer-events-none text-cyan-300 font-bold font-mono text-xs motion-safe:animate-bounce">
          <span>Z</span>
          <span className="text-[10px] -mt-1">z</span>
          <span className="text-[8px] -mt-1">z</span>
        </div>
      )}

      {/* Avatar Container with Cyan AI Gem Border Glow */}
      <div
        className={`relative ${sizeClasses} rounded-full overflow-hidden border-2 transition-all duration-300 ${
          state === "THINKING"
            ? "border-cyan-400 shadow-lg shadow-cyan-400/50 ring-2 ring-cyan-300"
            : state === "SUCCESS" || state === "CELEBRATION"
            ? "border-purple-400 shadow-lg shadow-purple-400/50 ring-2 ring-purple-300"
            : state === "SLEEPY"
            ? "border-slate-400 shadow-md shadow-slate-900/20"
            : "border-indigo-400 shadow-md shadow-indigo-300/40 ring-1 ring-cyan-400/60"
        } ${getMotionClass(state)} ${isInteractive ? "hover:scale-105 active:scale-95 cursor-pointer" : ""}`}
      >
        <Image
          src={getImageSource(state)}
          alt="Sir Paws-a-Lot - AI Study Cat Companion"
          width={imageSizes}
          height={imageSizes}
          className="w-full h-full object-cover object-center"
          priority
        />

        {/* Subtle Cyan AI Glow overlay at bottom (chest gem reflection) */}
        <div className="absolute inset-x-0 bottom-0 h-1/4 bg-gradient-to-t from-cyan-500/20 to-transparent pointer-events-none" />
      </div>

      {/* State Badge Pill */}
      {showBadge && size !== "sm" && (
        <div
          className={`absolute -bottom-2 z-20 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold shadow-md tracking-tight ${badge.color}`}
        >
          <BadgeIcon className="h-2.5 w-2.5 shrink-0" />
          <span>{badge.label}</span>
        </div>
      )}
    </div>
  );
}
