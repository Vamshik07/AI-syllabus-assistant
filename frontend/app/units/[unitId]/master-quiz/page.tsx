"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Quiz, QuizAttemptResponse, UnitDetail } from "@/types";
import QuizCard from "@/components/QuizCard";
import { Award, ChevronLeft, CheckCircle2, Lock } from "lucide-react";

export default function MasterQuizPage() {
  const params = useParams();
  const router = useRouter();
  const unitId = params.unitId as string;

  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [quizResult, setQuizResult] = useState<QuizAttemptResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [uData, qData] = await Promise.all([
        api.getUnit(unitId),
        api.generateMasterQuiz(unitId),
      ]);
      setUnit(uData);
      setQuiz(qData);
      if (qData) {
        try {
          const latestAttempt = await api.getLatestQuizAttempt(qData.id);
          if (latestAttempt) {
            setQuizResult(latestAttempt);
          }
        } catch (e) {
          // ignore
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load master quiz.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (unitId) {
      loadData();
    }
  }, [unitId]);

  const handleSuccess = (res: QuizAttemptResponse) => {
    setQuizResult(res);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent mb-3" />
        <p className="font-semibold text-gray-800 text-sm">Preparing Master Unit Quiz...</p>
        <p className="text-xs text-gray-500 mt-1">
          Generating comprehensive assessment across all completed topics in this unit.
        </p>
      </div>
    );
  }

  if (error || !unit || !quiz) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-sm text-red-700">
        <Lock className="h-8 w-8 mx-auto text-red-500 mb-2" />
        <p className="font-semibold">{error || "Master Quiz is locked."}</p>
        <p className="text-xs text-red-600 mt-1">
          You must complete and pass all individual topic quizzes in this unit first.
        </p>
        <Link
          href={`/units/${unitId}`}
          className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 underline"
        >
          <ChevronLeft className="h-4 w-4" /> Return to Unit
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          href={`/units/${unitId}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-indigo-600 transition-colors mb-3"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          <span>Back to Unit</span>
        </Link>

        <div className="flex items-center gap-2">
          <span className="rounded-md bg-amber-100 px-2.5 py-0.5 text-xs font-bold text-amber-800 flex items-center gap-1">
            <Award className="h-3.5 w-3.5" />
            Master Unit Assessment
          </span>
        </div>
        <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold text-gray-900">
          Master Quiz: {unit.title}
        </h1>
        <p className="text-xs sm:text-sm text-gray-600 mt-1">
          This final assessment covers at least 75% of the unit topics. It contains at least 25 questions and requires a score of 65% to complete the unit.
        </p>
      </div>

      <QuizCard
        quiz={quiz}
        topicTitle={`Master Assessment: ${unit.title}`}
        initialResult={quizResult}
        onSuccess={handleSuccess}
        onRetry={() => setQuizResult(null)}
      />
    </div>
  );
}
