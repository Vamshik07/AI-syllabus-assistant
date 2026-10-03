"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Subject, SubjectProgress, UnitProgress } from "@/types";
import { useAuth } from "@/context/AuthContext";
import ProgressBar from "@/components/ProgressBar";
import {
  BarChart3,
  CheckCircle2,
  Clock,
  Award,
  Layers,
  ChevronRight,
  BookOpen,
  Lock,
  LogIn,
  UserPlus,
} from "lucide-react";

export default function ProgressDashboardPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [progressData, setProgressData] = useState<Record<string, SubjectProgress>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAllProgress() {
      try {
        setLoading(true);
        const subjs = await api.getSubjects();
        setSubjects(subjs);

        const map: Record<string, SubjectProgress> = {};
        await Promise.all(
          subjs.map(async (s) => {
            try {
              const sp = await api.getSubjectProgress(s.id);
              map[s.id] = sp;
            } catch (e) {
              console.error(e);
            }
          })
        );
        setProgressData(map);
      } finally {
        setLoading(false);
      }
    }

    if (!authLoading) {
      if (isAuthenticated) {
        loadAllProgress();
      } else {
        setLoading(false);
      }
    }
  }, [isAuthenticated, authLoading]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <div className="flex items-center gap-2">
          <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700 flex items-center gap-1">
            <BarChart3 className="h-3.5 w-3.5" />
            Learning Analytics
          </span>
        </div>
        <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold text-gray-900">
          Curriculum Progress Tracking
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-gray-500">
          Hierarchical mastery tracking across Subjects, Units, and Topics.
        </p>
      </div>

      {!authLoading && !isAuthenticated ? (
        <div className="rounded-3xl border border-indigo-100 bg-white p-10 text-center shadow-lg shadow-indigo-50/50 max-w-lg mx-auto my-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 mx-auto mb-4">
            <Lock className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Sign In to Access Your Progress</h2>
          <p className="mt-2 text-xs text-gray-500 leading-relaxed">
            Your progress metrics, unit mastery, and quiz results are securely stored in your personal account.
          </p>
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/login"
              className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 transition-colors"
            >
              <LogIn className="h-4 w-4" />
              <span>Sign In to Account</span>
            </Link>
            <Link
              href="/register"
              className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl border border-gray-300 bg-white px-5 py-2.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <UserPlus className="h-4 w-4" />
              <span>Create Account</span>
            </Link>
          </div>
        </div>
      ) : loading ? (
        <div className="flex flex-col gap-4 animate-pulse">
          <div className="h-32 bg-gray-100 rounded-2xl border border-gray-200" />
          <div className="h-32 bg-gray-100 rounded-2xl border border-gray-200" />
        </div>
      ) : subjects.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-gray-300 bg-white p-12 text-center">
          <BarChart3 className="h-10 w-10 text-gray-400 mx-auto mb-2" />
          <h3 className="font-bold text-gray-800 text-sm">No progress data recorded yet</h3>
          <p className="mt-1 text-xs text-gray-500">
            Create a subject, upload units, and pass topic quizzes to see your mastery metrics.
          </p>
          <Link
            href="/subjects"
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
          >
            Go to Subjects
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {subjects.map((subj) => {
            const sp = progressData[subj.id];
            const completionPct = sp?.completion_percentage || 0;
            const unitsCompleted = sp?.units_completed || 0;
            const totalUnits = sp?.total_units || 0;

            return (
              <div
                key={subj.id}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
              >
                {/* Subject Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-gray-100 pb-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                      <BookOpen className="h-5 w-5" />
                    </div>
                    <div>
                      <Link
                        href={`/subjects/${subj.id}`}
                        className="font-bold text-gray-900 hover:text-indigo-600 text-base"
                      >
                        {subj.name}
                      </Link>
                      <p className="text-xs text-gray-500">
                        {unitsCompleted} of {totalUnits} Units Completed (Master Quiz Passed)
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${
                        completionPct === 100
                          ? "bg-emerald-100 text-emerald-800"
                          : completionPct > 0
                          ? "bg-indigo-100 text-indigo-800"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {completionPct}% Complete
                    </span>

                    <Link
                      href={`/subjects/${subj.id}`}
                      className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </Link>
                  </div>
                </div>

                <ProgressBar percentage={completionPct} showLabel={false} size="sm" className="mb-6" />

                {/* Unit breakdown */}
                {sp?.unit_progress && sp.unit_progress.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500">
                      Unit Breakdown
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {sp.unit_progress.map((up: UnitProgress) => (
                        <Link
                          key={up.unit_id}
                          href={`/units/${up.unit_id}`}
                          className="flex items-center justify-between rounded-xl border border-gray-100 bg-gray-50/60 p-3.5 hover:bg-gray-50 hover:border-gray-200 transition-colors"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-900 text-xs">
                                {up.unit_title}
                              </span>
                              {up.status === "COMPLETED" && (
                                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                              )}
                            </div>
                            <p className="text-[11px] text-gray-500 mt-0.5">
                              {up.topics_completed} / {up.total_topics} topics passed
                              {up.master_quiz_score !== null && up.master_quiz_score !== undefined && (
                                <span className="ml-1 text-emerald-700 font-medium">
                                  • Master Quiz: {up.master_quiz_score}/5
                                </span>
                              )}
                            </p>
                          </div>
                          <span className="font-mono text-xs font-bold text-gray-700">
                            {up.completion_percentage}%
                          </span>
                        </Link>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-gray-400">No units added yet.</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
