"use client";

import React from "react";
import { Topic, QuizAttemptResponse } from "@/types";
import {
  CheckCircle2,
  AlertTriangle,
  Award,
  RotateCcw,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Target,
  Sparkles,
} from "lucide-react";
import ProgressBar from "@/components/ProgressBar";

interface TopicProgressViewProps {
  topic: Topic;
  latestAttempt: QuizAttemptResponse | null;
  onRetakeQuiz: () => void;
  onReviewLearn: () => void;
}

export default function TopicProgressView({
  topic,
  latestAttempt,
  onRetakeQuiz,
  onReviewLearn,
}: TopicProgressViewProps) {
  const isPassed = topic.progress_status === "PASSED" || topic.progress_status === "COMPLETED";
  const score = latestAttempt ? latestAttempt.percentage : 0;
  const passed = latestAttempt ? latestAttempt.passed : isPassed;

  return (
    <div className="flex flex-col gap-6 max-w-3xl mx-auto w-full">
      {/* Overview Card */}
      <div className="rounded-3xl border border-gray-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-gray-100">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700">
                Topic {topic.order_index}
              </span>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-bold border ${
                  passed
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-amber-50 text-amber-700 border-amber-200"
                }`}
              >
                {passed ? "Mastery Achieved" : "In Progress"}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-gray-900 mt-2">
              {topic.name}
            </h2>
          </div>

          <div className="flex flex-col items-start sm:items-end">
            <span className="text-xs text-gray-500 font-medium">Latest Quiz Score</span>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span
                className={`text-3xl font-black ${
                  passed ? "text-emerald-600" : "text-amber-600"
                }`}
              >
                {latestAttempt ? Math.round(score) : isPassed ? "75+" : "0"}%
              </span>
              <span className="text-xs font-bold text-gray-400">/ 75% required</span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <ProgressBar percentage={latestAttempt ? Math.round(score) : isPassed ? 100 : 20} size="md" />
        </div>

        {/* Status Highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
          <div className="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
            <div className="text-xs font-semibold text-gray-500">Status</div>
            <div className="mt-1 font-bold text-gray-900 text-sm">
              {topic.progress_status || "UNLOCKED"}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
            <div className="text-xs font-semibold text-gray-500">Passing Criteria</div>
            <div className="mt-1 font-bold text-gray-900 text-sm">Score &ge; 75% (3/4 or 4/5)</div>
          </div>

          <div className="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
            <div className="text-xs font-semibold text-gray-500">Next Step</div>
            <div className="mt-1 font-bold text-gray-900 text-sm">
              {passed ? "Advance to Next Topic" : "Review & Retake Quiz"}
            </div>
          </div>
        </div>
      </div>

      {/* Weak Concept Breakdown if attempt exists */}
      {latestAttempt?.weak_concepts && latestAttempt.weak_concepts.length > 0 && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            <h3 className="font-bold text-amber-950 text-sm">Concepts to Strengthen</h3>
          </div>
          <p className="text-xs text-amber-800 mb-3">
            Your recent assessment revealed opportunities to review these specific areas before final exams:
          </p>
          <div className="flex flex-wrap gap-2">
            {latestAttempt.weak_concepts.map((concept, i) => (
              <span
                key={i}
                className="rounded-xl border border-amber-300 bg-white px-3 py-1 text-xs font-bold text-amber-900 shadow-2xs"
              >
                {concept}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Concept Breakdown Table if available */}
      {latestAttempt?.concept_breakdown && (
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="font-bold text-gray-900 text-sm mb-4">Assessment Concept Breakdown</h3>
          <div className="flex flex-col gap-3">
            {Object.entries(latestAttempt.concept_breakdown).map(([area, data]) => (
              <div key={area} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-gray-800">{area}</span>
                  <span className="font-semibold text-gray-500">
                    {data.correct} / {data.total} ({Math.round(data.percentage)}%)
                  </span>
                </div>
                <ProgressBar percentage={Math.round(data.percentage)} size="sm" showLabel={false} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={onReviewLearn}
          className="flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-5 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 shadow-2xs transition-colors"
        >
          <BookOpen className="h-4 w-4" />
          <span>Review Structured Notes</span>
        </button>

        <button
          onClick={onRetakeQuiz}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 transition-all hover:scale-105"
        >
          <RotateCcw className="h-4 w-4" />
          <span>{passed ? "Practice Again" : "Retake Topic Quiz"}</span>
        </button>
      </div>
    </div>
  );
}
