"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Quiz, QuizAttemptResponse } from "@/types";
import { api } from "@/lib/api";
import { CheckCircle2, XCircle, HelpCircle, ArrowRight, RotateCcw, Award, BrainCircuit, Sparkles, BookOpen, AlertTriangle, Lightbulb } from "lucide-react";
import { useCatCompanion } from "@/context/CatCompanionContext";

interface QuizCardProps {
  quiz: Quiz;
  topicTitle: string;
  initialResult?: QuizAttemptResponse | null;
  onSuccess: (result: QuizAttemptResponse) => void;
  onRetry: () => void;
  onFreshQuestions?: () => Promise<void>;
}

export default function QuizCard({
  quiz,
  topicTitle,
  initialResult,
  onSuccess,
  onRetry,
  onFreshQuestions,
}: QuizCardProps) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [result, setResult] = useState<QuizAttemptResponse | null>(initialResult || null);
  const [error, setError] = useState<string | null>(null);

  const { setCatState, triggerSpeechBubble, openChat, setCompanionContext } = useCatCompanion();

  useEffect(() => {
    if (initialResult !== undefined) {
      setResult(initialResult);
    }
  }, [initialResult]);

  const questions = quiz.questions || [];
  const currentQuestion = questions[currentIdx];

  // Sync active question into companion context
  useEffect(() => {
    if (currentQuestion) {
      setCompanionContext({ currentQuestion: currentQuestion.question });
    }
  }, [currentQuestion, setCompanionContext]);

  const handleSelectOption = (option: string) => {
    if (result) return; // Locked after submission
    setSelectedAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: option,
    }));
  };

  const handleSubmit = async () => {
    setError(null);
    if (Object.keys(selectedAnswers).length < questions.length) {
      setError("Please answer all questions before submitting.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await api.submitQuizAttempt(quiz.id, selectedAnswers);
      setResult(res);
      if (res.passed) {
        setCatState("SUCCESS");
        triggerSpeechBubble("HUZZAH! Splendid victory! You passed this topic quest! 🎉⚔️", 8000, "SUCCESS");
        onSuccess(res);
      } else {
        setCatState("SUPPORTIVE");
        triggerSpeechBubble("That's okay, brave scholar! Let's review the weak concepts and master it together! 🐾", 8000, "SUPPORTIVE");
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit quiz attempt.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSelectedAnswers({});
    setResult(null);
    setCurrentIdx(0);
    onRetry();
  };

  const handleFreshQuestions = async () => {
    setIsRegenerating(true);
    setError(null);
    try {
      // First regenerate on the server
      if (quiz.topic_id) {
        await api.generateTopicQuiz(quiz.topic_id, true);
      }
      // Then let the parent re-fetch with the new quiz ID
      if (onFreshQuestions) {
        await onFreshQuestions();
      } else {
        handleReset();
      }
    } catch (err: any) {
      setError(err.message || "Failed to generate fresh questions.");
      setIsRegenerating(false);
    }
    // Note: isRegenerating will be cleared by the parent re-mount
  };

  if (!currentQuestion && !result) {
    return (
      <div className="p-8 text-center text-gray-500">
        No questions available for this quiz.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 sm:p-8 shadow-sm">
      {result ? (
        /* Results View */
        <div className="flex flex-col gap-6">
          {/* Hero Banner */}
          <div
            className={`rounded-2xl p-6 text-center border ${
              result.passed
                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                : "bg-red-50 border-red-200 text-red-900"
            }`}
          >
            <div className="flex justify-center mb-3">
              {result.passed ? (
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-600 text-white shadow-md shadow-emerald-200">
                  <Award className="h-8 w-8" />
                </div>
              ) : (
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-600 text-white shadow-md shadow-red-200">
                  <XCircle className="h-8 w-8" />
                </div>
              )}
            </div>

            <h3 className="text-2xl font-extrabold">
              {result.passed ? "Quiz Passed Successfully!" : "Quiz Not Passed"}
            </h3>
            <p className="mt-1 text-sm font-medium">
              You scored <span className="font-bold">{result.score}</span> out of{" "}
              <span className="font-bold">{result.total_questions}</span> ({result.percentage}%)
            </p>

            {result.passed ? (
              <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 border border-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Passed! Minimum requirement ({result.passing_percentage}%) achieved</span>
              </div>
            ) : (
              <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-800 border border-red-200">
                <XCircle className="h-3.5 w-3.5" />
                <span>Minimum {result.passing_percentage}% score required. Review weak concepts and retry!</span>
              </div>
            )}
          </div>

          {/* 4 Metric Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border border-gray-200 bg-gray-50/70 p-3.5 text-center">
              <span className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Attempted</span>
              <p className="mt-1 text-lg font-extrabold text-gray-900">{questions.length}</p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3.5 text-center">
              <span className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Correct</span>
              <p className="mt-1 text-lg font-extrabold text-emerald-700">{result.score}</p>
            </div>
            <div className="rounded-xl border border-red-200 bg-red-50/50 p-3.5 text-center">
              <span className="text-[11px] font-semibold text-red-700 uppercase tracking-wider">Incorrect</span>
              <p className="mt-1 text-lg font-extrabold text-red-700">{result.total_questions - result.score}</p>
            </div>
            <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3.5 text-center">
              <span className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider">Grade</span>
              <p className="mt-1 text-lg font-extrabold text-indigo-700">{result.percentage}%</p>
            </div>
          </div>

          {/* Weak Concept Detection & Concept Mastery Breakdown */}
          {result.concept_breakdown && Object.keys(result.concept_breakdown).length > 0 && (
            <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/60 to-purple-50/40 p-5">
              <div className="flex items-center gap-2 mb-3">
                <BrainCircuit className="h-5 w-5 text-indigo-600" />
                <h4 className="font-bold text-gray-900 text-sm">Topic Concept Map & Mastery Breakdown</h4>
              </div>
              <p className="text-xs text-gray-600 mb-4">
                Understanding is evaluated across the distinct learning elements of this topic.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(result.concept_breakdown).map(([area, stats]) => {
                  const isMastered = stats.percentage >= 65.0;
                  return (
                    <div
                      key={area}
                      className={`rounded-xl border p-3 bg-white/90 shadow-2xs ${
                        isMastered ? "border-emerald-200" : "border-amber-200"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <span className="font-semibold text-gray-800">{area}</span>
                        <span
                          className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                            isMastered
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {stats.percentage}% ({stats.correct}/{stats.total})
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-1.5 rounded-full transition-all ${
                            isMastered ? "bg-emerald-500" : "bg-amber-500"
                          }`}
                          style={{ width: `${Math.max(5, stats.percentage)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Targeted Revision Recommendations */}
              {result.recommended_revision && result.recommended_revision.length > 0 && (
                <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/80 p-3.5 text-xs text-amber-900">
                  <div className="flex items-center gap-2 font-bold mb-1.5">
                    <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                    <span>Recommended Revision for Weak Concepts</span>
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-amber-800 pl-1">
                    {result.recommended_revision.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Breakdown of questions */}
          <div className="flex flex-col gap-4">
            <h4 className="font-bold text-gray-900 text-sm">Detailed Question Review & Checked Answers</h4>
            {result.results.map((r, idx) => (
              <div
                key={r.question_id}
                className={`rounded-xl border p-4 text-xs transition-colors ${
                  r.is_correct ? "border-emerald-200 bg-emerald-50/40" : "border-red-200 bg-red-50/40"
                }`}
              >
                <div className="flex items-start gap-2.5">
                  {r.is_correct ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      {r.concept_area && (
                        <span className="rounded-md bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-semibold text-indigo-700">
                          {r.concept_area}
                        </span>
                      )}
                      {r.question_type && (
                        <span className="rounded-md bg-gray-100 border border-gray-200 px-2 py-0.5 text-[10px] font-medium text-gray-700 capitalize">
                          {r.question_type.replace('_', ' ')}
                        </span>
                      )}
                      {r.difficulty && (
                        <span className="rounded-md bg-purple-50 border border-purple-200 px-2 py-0.5 text-[10px] font-medium text-purple-700 capitalize">
                          {r.difficulty}
                        </span>
                      )}
                    </div>

                    <p className="font-bold text-gray-900 text-sm">
                      Question {idx + 1}: {r.question}
                    </p>
                    <div className="mt-2.5 space-y-1.5 text-xs text-gray-700">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-500">Your Checked Answer:</span>
                        <span className={`inline-block px-2 py-0.5 rounded font-medium ${
                          r.is_correct ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                        }`}>
                          {r.selected_answer || "Not answered"}
                        </span>
                      </div>
                      {!r.is_correct && (
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-500">Correct Answer:</span>
                          <span className="inline-block px-2 py-0.5 rounded font-medium bg-emerald-100 text-emerald-800">
                            {r.correct_answer}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Source reference citation */}
                    <div className="mt-3 rounded-lg bg-white/90 p-3 border border-gray-200 text-xs text-gray-600 shadow-2xs">
                      <p className="font-semibold text-gray-800 flex items-center gap-1.5 mb-1">
                        <HelpCircle className="h-3.5 w-3.5 text-indigo-600" />
                        Source Reference Citation:
                      </p>
                      <p className="italic text-gray-700">&ldquo;{r.source_reference}&rdquo;</p>
                      {r.explanation && (
                        <p className="mt-1 text-gray-500">{r.explanation}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-5">
            <div className="flex items-center gap-2">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-xs font-semibold text-gray-700 shadow-sm hover:bg-gray-50"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Retry Quiz</span>
              </button>

              {quiz.topic_id && (
                <button
                  onClick={handleFreshQuestions}
                  disabled={isRegenerating}
                  className="flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-xs font-semibold text-indigo-700 shadow-2xs hover:bg-indigo-100 disabled:opacity-50"
                >
                  <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                  <span>{isRegenerating ? "Generating..." : "Practice Fresh Questions"}</span>
                </button>
              )}
            </div>

            {/* If PASSED, show Next Topic button */}
            {result.passed ? (
              <div className="flex items-center gap-2">
                {result.unlocked_next_topic_id ? (
                  <Link
                    href={`/topics/${result.unlocked_next_topic_id}`}
                    className="flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 transition-transform hover:scale-105"
                  >
                    <span>Next Topic Unlocked</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : result.master_quiz_unlocked ? (
                  <Link
                    href={`/units/${quiz.unit_id}/master-quiz`}
                    className="flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-2.5 text-xs font-bold text-white shadow-md hover:bg-emerald-700 transition-transform hover:scale-105"
                  >
                    <Award className="h-4 w-4" />
                    <span>Take Master Unit Quiz</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : (
                  <Link
                    href={`/units/${quiz.unit_id}`}
                    className="flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 transition-transform hover:scale-105"
                  >
                    <span>Back to Unit Pathway</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                )}
              </div>
            ) : (
              <span className="text-xs text-red-600 font-medium">
                Pass this quiz to unlock the next topic.
              </span>
            )}
          </div>
        </div>
      ) : (

        /* Taking Quiz View */
        <div className="flex flex-col gap-6">
          {/* Header & Question Indicators */}
          <div className="flex items-center justify-between border-b border-gray-100 pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                Topic Assessment
              </span>
              <h3 className="text-lg font-bold text-gray-900">{topicTitle}</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() =>
                  openChat(
                    `Can you give me a subtle hint for this question: "${currentQuestion.question}"?`
                  )
                }
                title="Ask Sir Paws-a-Lot for a hint"
                className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs font-bold text-amber-800 hover:bg-amber-100 transition-colors shadow-2xs"
              >
                <Lightbulb className="h-3.5 w-3.5 text-amber-600" />
                <span>Ask Cat for Hint 💡</span>
              </button>
              <span className="rounded-full bg-indigo-50 px-3 py-1 font-mono text-xs font-bold text-indigo-700">
                Question {currentIdx + 1} of {questions.length}
              </span>
            </div>
          </div>

          {/* Stepper bubbles */}
          <div className="flex items-center gap-2">
            {questions.map((q, idx) => {
              const answered = !!selectedAnswers[q.id];
              const isCurrent = idx === currentIdx;
              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentIdx(idx)}
                  className={`h-2.5 flex-1 rounded-full transition-all ${
                    isCurrent
                      ? "bg-indigo-600"
                      : answered
                      ? "bg-indigo-300"
                      : "bg-gray-200"
                  }`}
                />
              );
            })}
          </div>

          {/* Question Text */}
          <div className="py-2">
            <h4 className="text-base font-semibold text-gray-900 leading-snug">
              {currentQuestion.question}
            </h4>
          </div>

          {/* Options List */}
          <div className="flex flex-col gap-3">
            {currentQuestion.options.map((opt, oIdx) => {
              const isSelected = selectedAnswers[currentQuestion.id] === opt;
              return (
                <button
                  key={oIdx}
                  onClick={() => handleSelectOption(opt)}
                  className={`flex items-center justify-between rounded-xl border p-4 text-left text-sm transition-all ${
                    isSelected
                      ? "border-indigo-600 bg-indigo-50/60 text-indigo-950 font-medium shadow-sm ring-1 ring-indigo-600"
                      : "border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                        isSelected
                          ? "bg-indigo-600 text-white"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {String.fromCharCode(65 + oIdx)}
                    </span>
                    <span>{opt}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
              {error}
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex items-center justify-between border-t border-gray-100 pt-4">
            <button
              onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
              disabled={currentIdx === 0}
              className="rounded-lg px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-40"
            >
              Previous
            </button>

            {currentIdx < questions.length - 1 ? (
              <button
                onClick={() => setCurrentIdx((prev) => prev + 1)}
                className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
              >
                <span>Next Question</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60"
              >
                {isSubmitting ? "Submitting..." : "Submit Quiz"}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
