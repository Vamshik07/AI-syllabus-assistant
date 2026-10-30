"use client";

import React, { useState } from "react";
import { Topic, TopicContentView } from "@/types";
import {
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Layers,
} from "lucide-react";

interface PracticeCard {
  front: string;
  back: string;
  concept_area?: string;
  source_reference?: string;
}

interface TopicPracticeCardsProps {
  topic: Topic;
  content: TopicContentView;
}

export default function TopicPracticeCards({ topic, content }: TopicPracticeCardsProps) {
  const cards: PracticeCard[] =
    content.learning_data?.practice_cards ||
    topic.learning_data?.practice_cards ||
    [];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [masteredIds, setMasteredIds] = useState<Set<number>>(new Set());
  const [reviewIds, setReviewIds] = useState<Set<number>>(new Set());

  if (cards.length === 0) {
    return (
      <div className="rounded-2xl border-2 border-dashed border-gray-200 bg-white p-12 text-center">
        <Layers className="h-10 w-10 text-gray-300 mx-auto mb-3" />
        <h3 className="font-bold text-gray-800 text-sm">No practice cards generated yet</h3>
        <p className="mt-1 text-xs text-gray-500 max-w-sm mx-auto">
          Practice flashcards are automatically generated from core concepts and definitions once study material is loaded.
        </p>
      </div>
    );
  }

  const currentCard = cards[currentIndex];

  const handleNext = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % cards.length);
  };

  const handlePrev = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + cards.length) % cards.length);
  };

  const markMastered = () => {
    setMasteredIds((prev) => new Set(prev).add(currentIndex));
    setReviewIds((prev) => {
      const next = new Set(prev);
      next.delete(currentIndex);
      return next;
    });
    handleNext();
  };

  const markNeedsReview = () => {
    setReviewIds((prev) => new Set(prev).add(currentIndex));
    setMasteredIds((prev) => {
      const next = new Set(prev);
      next.delete(currentIndex);
      return next;
    });
    handleNext();
  };

  const handleReset = () => {
    setCurrentIndex(0);
    setIsFlipped(false);
    setMasteredIds(new Set());
    setReviewIds(new Set());
  };

  return (
    <div className="flex flex-col items-center gap-6 max-w-2xl mx-auto w-full">
      {/* Top Controls & Counter */}
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-gray-700">
            Card {currentIndex + 1} of {cards.length}
          </span>
          <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700 border border-emerald-200">
            {masteredIds.size} Mastered
          </span>
          {reviewIds.size > 0 && (
            <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold text-amber-700 border border-amber-200">
              {reviewIds.size} Review
            </span>
          )}
        </div>

        <button
          onClick={handleReset}
          className="flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-indigo-600 transition-colors"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>Reset Session</span>
        </button>
      </div>

      {/* Flashcard Frame */}
      <div
        onClick={() => setIsFlipped(!isFlipped)}
        className="group relative flex min-h-[300px] sm:min-h-[340px] w-full cursor-pointer flex-col justify-between rounded-3xl border-2 border-indigo-100 bg-white p-8 shadow-md hover:border-indigo-300 hover:shadow-lg transition-all"
      >
        <div className="flex items-center justify-between">
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
            {currentCard.concept_area || "Core Concept"}
          </span>
          {currentCard.source_reference && (
            <span className="text-xs text-gray-400 font-medium">
              {currentCard.source_reference}
            </span>
          )}
        </div>

        {/* Content Body */}
        <div className="my-auto py-6 text-center">
          <p className="text-xs font-semibold text-indigo-500 uppercase tracking-wider mb-2">
            {isFlipped ? "Explanation / Answer" : "Question / Concept Prompt"}
          </p>
          <h3 className="text-lg sm:text-xl font-extrabold text-gray-900 leading-relaxed">
            {isFlipped ? currentCard.back : currentCard.front}
          </h3>
        </div>

        {/* Flip hint footer */}
        <div className="flex items-center justify-center text-xs font-semibold text-gray-400 group-hover:text-indigo-600 transition-colors">
          <Sparkles className="h-3.5 w-3.5 mr-1.5" />
          <span>{isFlipped ? "Click card to flip back to question" : "Click card to reveal answer"}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between w-full gap-4">
        <button
          onClick={handlePrev}
          className="flex items-center gap-1 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 shadow-2xs transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Previous</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={markNeedsReview}
            className="flex items-center gap-1.5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs font-bold text-amber-800 hover:bg-amber-100 shadow-2xs transition-colors"
          >
            <AlertCircle className="h-4 w-4" />
            <span>Need Review</span>
          </button>
          <button
            onClick={markMastered}
            className="flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 shadow-sm transition-colors"
          >
            <CheckCircle2 className="h-4 w-4" />
            <span>Know It!</span>
          </button>
        </div>

        <button
          onClick={handleNext}
          className="flex items-center gap-1 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 shadow-2xs transition-colors"
        >
          <span>Next</span>
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
