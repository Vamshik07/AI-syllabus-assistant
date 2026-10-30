"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Topic, TopicContentView, Quiz, QuizAttemptResponse } from "@/types";
import SourceContentViewer from "@/components/SourceContentViewer";
import QuizCard from "@/components/QuizCard";
import TopicLearnView from "@/components/topic/TopicLearnView";
import TopicVisualsGallery from "@/components/topic/TopicVisualsGallery";
import TopicKeywordsView from "@/components/topic/TopicKeywordsView";
import TopicPracticeCards from "@/components/topic/TopicPracticeCards";
import TopicProgressView from "@/components/topic/TopicProgressView";
import {
  ChevronLeft,
  BookOpen,
  FileText,
  Image as ImageIcon,
  Tag,
  HelpCircle,
  Layers,
  BarChart2,
  MessageSquare,
  CheckCircle2,
  Award,
} from "lucide-react";
import { useCatCompanion } from "@/context/CatCompanionContext";

type TabKey =
  | "information"
  | "keywords"
  | "diagrams"
  | "quiz"
  | "practice"
  | "progress";

export default function TopicLearningPage() {
  const params = useParams();
  const router = useRouter();
  const topicId = params.topicId as string;

  const [topic, setTopic] = useState<Topic | null>(null);
  const [content, setContent] = useState<TopicContentView | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [quizResult, setQuizResult] = useState<QuizAttemptResponse | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("information");
  const [loading, setLoading] = useState(true);
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setCatState, triggerSpeechBubble, setCompanionContext, openChat } = useCatCompanion();

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
      const currentQuiz = await api.getTopicQuiz(topicId);
      setQuiz(currentQuiz);

      if (currentQuiz) {
        try {
          const latestAttempt = await api.getLatestQuizAttempt(currentQuiz.id);
          setQuizResult(latestAttempt || null);
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
    setQuizResult(result);
    try {
      const updatedTopic = await api.getTopic(topicId);
      setTopic(updatedTopic);
    } catch (err) {
      console.error("Failed to refresh topic status:", err);
    }
  };

  const handleFreshQuestionsRequested = async () => {
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
        <div className="h-12 w-full bg-gray-200 rounded-xl" />
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
  const visualCount = content.learning_data?.visuals?.length || 0;
  const keywordCount = content.learning_data?.keywords?.length || 0;
  const pyqFrequency = content.pyq_frequency || topic.pyq_frequency || 0;

  const tabs: Array<{ key: TabKey; label: string; icon: any; badge?: number | string }> = [
    { key: "information", label: "Information", icon: BookOpen },
    { key: "keywords", label: "Important Key Words", icon: Tag, badge: keywordCount > 0 ? keywordCount : undefined },
    ...(visualCount > 0
      ? [{ key: "diagrams" as TabKey, label: "Diagrams", icon: ImageIcon, badge: visualCount }]
      : []),
    { key: "quiz", label: "Quiz", icon: HelpCircle, badge: isPassed ? "✓" : undefined },
    { key: "practice", label: "Practice", icon: Layers },
    { key: "progress", label: "Progress", icon: BarChart2 },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Header & Breadcrumb */}
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
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700">
                Topic {topic.order_index}
              </span>
              {isPassed && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-bold text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Quiz Passed
                </span>
              )}
              {pyqFrequency > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-bold text-amber-800 border border-amber-200">
                  <Award className="h-3.5 w-3.5" />
                  PYQ Frequent ({pyqFrequency}x)
                </span>
              )}
            </div>
            <h1 className="mt-1.5 text-2xl sm:text-3xl font-extrabold text-gray-900">
              {topic.name}
            </h1>
          </div>

          {/* Quick AI Mascot Trigger */}
          <button
            onClick={() => {
              setCatState("EXPLAINING");
              openChat(`Explain the key concepts of ${topic.name}`);
            }}
            className="inline-flex items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50/70 px-4 py-2 text-xs font-bold text-indigo-700 hover:bg-indigo-100 transition-all self-start sm:self-auto shadow-2xs"
          >
            <MessageSquare className="h-4 w-4 text-indigo-600" />
            <span>Ask Sir Paws-a-Lot</span>
          </button>
        </div>
      </div>

      {/* Modern Scrollable Tab Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-gray-200 scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => {
                if (tab.key === "quiz") {
                  handleStartQuiz();
                } else {
                  setActiveTab(tab.key);
                }
              }}
              className={`flex items-center gap-1.5 whitespace-nowrap rounded-xl px-3.5 py-2 text-xs font-bold transition-all ${
                isActive
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-gray-600 hover:bg-gray-100 hover:text-gray-900 border border-gray-100"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-extrabold ${
                    isActive ? "bg-white/20 text-white" : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "information" && (
          <TopicLearnView
            topic={topic}
            content={content}
            onSelectTab={(newTab: TabKey) => {
              if (newTab === "quiz") {
                handleStartQuiz();
              } else {
                setActiveTab(newTab);
              }
            }}
          />
        )}

        {activeTab === "keywords" && <TopicKeywordsView topic={topic} content={content} />}

        {activeTab === "diagrams" && <TopicVisualsGallery content={content} />}

        {activeTab === "quiz" && (
          <div>
            {loadingQuiz ? (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white p-12 text-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent mb-3" />
                <p className="font-semibold text-gray-800 text-sm">Preparing topic quiz...</p>
                <p className="text-xs text-gray-500 mt-1">
                  Loading source-grounded questions and diagnostic feedback.
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

        {activeTab === "practice" && <TopicPracticeCards topic={topic} content={content} />}

        {activeTab === "progress" && (
          <TopicProgressView
            topic={topic}
            latestAttempt={quizResult}
            onRetakeQuiz={handleStartQuiz}
            onReviewLearn={() => setActiveTab("information")}
          />
        )}
      </div>
    </div>
  );
}
