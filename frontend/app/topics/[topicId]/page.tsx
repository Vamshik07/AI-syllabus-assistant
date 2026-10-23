"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Topic, TopicContentView, Quiz, QuizAttemptResponse } from "@/types";
import SourceContentViewer from "@/components/SourceContentViewer";
import QuizCard from "@/components/QuizCard";
import {
  ChevronLeft,
  BookOpen,
  HelpCircle,
  CheckCircle2,
  Lock,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
} from "lucide-react";
import { useCatCompanion } from "@/context/CatCompanionContext";

export default function TopicLearningPage() {
  const params = useParams();
  const router = useRouter();
  const topicId = params.topicId as string;

  const [topic, setTopic] = useState<Topic | null>(null);
  const [content, setContent] = useState<TopicContentView | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [quizResult, setQuizResult] = useState<QuizAttemptResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"content" | "quiz">("content");
  const [loading, setLoading] = useState(true);
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setCatState, triggerSpeechBubble, setCompanionContext } = useCatCompanion();

  const loadTopicAndContent = async () => {
    try {
      setLoading(true);
      const [tData, cData] = await Promise.all([
        api.getTopic(topicId),
        api.getTopicContent(topicId),
      ]);
      setTopic(tData);
      setContent(cData);
      setCompanionContext({
        topicId: tData.id,
        topicName: tData.name,
        unitId: cData.unit_id || undefined,
        unitTitle: cData.unit_title || undefined,
        subjectId: cData.subject_id || undefined,
        subjectName: cData.subject_name || undefined,
        pageType: "topic",
      });
      setCatState("STUDYING");
      triggerSpeechBubble(`Studying ${tData.name}? Need an explanation or example? 🐱📚`, 7000, "STUDYING");
    } catch (err: any) {
      setError(err.message || "Failed to load topic content.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (topicId) {
      loadTopicAndContent();
    }
  }, [topicId]);

  const handleStartQuiz = async () => {
    setActiveTab("quiz");
    setLoadingQuiz(true);
    setError(null);
    setCatState("QUIZ");
    triggerSpeechBubble("Focus, brave scholar! Tap me if you need a conceptual hint. ⚔️", 6000, "QUIZ");
    try {
      // Always fetch current quiz from server to avoid stale ID after any regeneration
      const currentQuiz = await api.getTopicQuiz(topicId);
      setQuiz(currentQuiz);

      // Fetch latest attempt if available
      if (currentQuiz) {
        try {
          const latestAttempt = await api.getLatestQuizAttempt(currentQuiz.id);
          if (latestAttempt) {
            setQuizResult(latestAttempt);
          } else {
            setQuizResult(null);
          }
        } catch (e) {
          setQuizResult(null);
        }
      }
    } catch (err: any) {
      alert(err.message || "Failed to load topic quiz.");
    } finally {
      setLoadingQuiz(false);
    }
  };

  const handleQuizSuccess = async (result: QuizAttemptResponse) => {
    // Keep the result visible immediately! Do NOT show loading pulse which unmounts QuizCard!
    setQuizResult(result);
    try {
      const updatedTopic = await api.getTopic(topicId);
      setTopic(updatedTopic);
    } catch (err) {
      console.error("Failed to refresh topic status:", err);
    }
  };

  const handleFreshQuestionsRequested = async () => {
    // Called by QuizCard "Practice Fresh Questions" button.
    // Re-fetches the newly regenerated quiz so the correct ID is used.
    setLoadingQuiz(true);
    setQuizResult(null);
    try {
      const freshQuiz = await api.getTopicQuiz(topicId);
      setQuiz(freshQuiz);
    } catch (err: any) {
      console.error("Failed to reload fresh quiz:", err);
    } finally {
      setLoadingQuiz(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-6 animate-pulse">
        <div className="h-6 w-32 bg-gray-200 rounded" />
        <div className="h-10 w-72 bg-gray-200 rounded-lg" />
        <div className="h-96 bg-gray-100 rounded-2xl border border-gray-200" />
      </div>
    );
  }

  if (error || !topic || !content) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-sm text-red-700">
        <p className="font-semibold">{error || "Unable to display topic content."}</p>
        <button
          onClick={() => router.back()}
          className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 underline"
        >
          <ChevronLeft className="h-4 w-4" /> Return to Unit
        </button>
      </div>
    );
  }

  const isPassed = topic.progress_status === "PASSED" || topic.progress_status === "COMPLETED";

  return (
    <div className="flex flex-col gap-6">
      {/* Navigation & Header */}
      <div>
        <button
          onClick={() => router.back()}
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-indigo-600 transition-colors mb-3"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          <span>Return to Unit Pathway</span>
        </button>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700">
                Topic {topic.order_index}
              </span>
              {isPassed && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-bold text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Quiz Passed
                </span>
              )}
            </div>
            <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold text-gray-900">
              {topic.name}
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setActiveTab("content");
                setCatState("STUDYING");
              }}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "content"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              <BookOpen className="h-4 w-4" />
              <span>Source Learning Material</span>
            </button>

            <button
              onClick={handleStartQuiz}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "quiz"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : isPassed
                  ? "bg-emerald-50 border border-emerald-300 text-emerald-800 hover:bg-emerald-100"
                  : "bg-amber-500 text-white shadow-sm hover:bg-amber-600 hover:scale-105"
              }`}
            >
              <HelpCircle className="h-4 w-4" />
              <span>{isPassed ? (quizResult ? "Quiz Results" : "Topic Quiz") : "Take Topic Quiz"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main View Area */}
      {activeTab === "content" ? (
        <div className="flex flex-col gap-6">
          <SourceContentViewer content={content} />

          {/* Bottom call to action for assessment */}
          <div className="flex items-center justify-between rounded-2xl border border-indigo-200 bg-indigo-50/50 p-6">
            <div>
              <h4 className="font-bold text-indigo-950 text-sm">
                {isPassed ? "Topic Assessment Passed!" : "Finished studying this topic?"}
              </h4>
              <p className="text-xs text-indigo-700 mt-0.5">
                {isPassed
                  ? "You have already passed this topic. You can review your quiz results or practice again."
                  : "Take the 5-question assessment to test and track your topic mastery."}
              </p>
            </div>
            <button
              onClick={handleStartQuiz}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 transition-transform hover:scale-105"
            >
              <span>{isPassed ? "View Quiz Results" : "Take Topic Quiz"}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      ) : (
        /* Quiz View */
        <div>
          {loadingQuiz ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white p-12 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent mb-3" />
              <p className="font-semibold text-gray-800 text-sm">Preparing topic quiz...</p>
              <p className="text-xs text-gray-500 mt-1">
                Loading source-grounded questions and previous assessment results.
              </p>
            </div>
          ) : quiz ? (
            <QuizCard
              quiz={quiz}
              topicTitle={topic.name}
              initialResult={quizResult}
              onSuccess={handleQuizSuccess}
              onRetry={() => {
                setQuizResult(null);
              }}
              onFreshQuestions={handleFreshQuestionsRequested}
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
