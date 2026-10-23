"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { UnitDetail, DocumentInfo, Topic } from "@/types";
import DocumentUploader from "@/components/DocumentUploader";
import ProgressBar from "@/components/ProgressBar";
import {
  ChevronLeft,
  CheckCircle2,
  Lock,
  ArrowRight,
  Award,
  Sparkles,
  BookOpen,
  FileText,
  AlertCircle,
  Pencil,
  Trash2,
} from "lucide-react";
import { useCatCompanion } from "@/context/CatCompanionContext";

export default function UnitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const unitId = params.unitId as string;

  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { setCatState, triggerSpeechBubble, setCompanionContext } = useCatCompanion();

  // Edit / Delete Unit state
  const [showEditUnit, setShowEditUnit] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [updatingUnit, setUpdatingUnit] = useState(false);

  const [showDeleteUnit, setShowDeleteUnit] = useState(false);
  const [deletingUnit, setDeletingUnit] = useState(false);

  const loadUnit = async () => {
    try {
      setLoading(true);
      const data = await api.getUnit(unitId);
      setUnit(data);
      setCompanionContext({
        unitId: data.id,
        unitTitle: data.title,
        subjectId: data.subject_id,
        pageType: "units",
      });
      setCatState("IDLE");
      triggerSpeechBubble(`Unit: ${data.title}! Ready to dive into the topics? 🐱⚔️`, 6000);
    } catch (err: any) {
      setError(err.message || "Failed to load unit details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (unitId) {
      loadUnit();
    }
  }, [unitId]);

  const handleDocumentUploaded = (doc: DocumentInfo) => {
    loadUnit();
  };

  const handleUpdateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTitle.trim()) return;
    try {
      setUpdatingUnit(true);
      await api.updateUnit(unitId, {
        title: editTitle.trim(),
        description: editDesc.trim() || undefined,
      });
      setShowEditUnit(false);
      loadUnit();
    } catch (err: any) {
      alert(err.message || "Failed to update unit.");
    } finally {
      setUpdatingUnit(false);
    }
  };

  const handleDeleteUnit = async () => {
    try {
      setDeletingUnit(true);
      await api.deleteUnit(unitId);
      router.push(`/subjects/${unit?.subject_id}`);
    } catch (err: any) {
      alert(err.message || "Failed to delete unit.");
      setDeletingUnit(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-6 animate-pulse">
        <div className="h-6 w-32 bg-gray-200 rounded" />
        <div className="h-24 bg-gray-100 rounded-2xl border border-gray-200" />
        <div className="h-64 bg-gray-100 rounded-2xl border border-gray-200" />
      </div>
    );
  }

  if (error || !unit) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-sm text-red-700">
        <p className="font-semibold">{error || "Unit not found."}</p>
        <Link
          href="/subjects"
          className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 underline"
        >
          <ChevronLeft className="h-4 w-4" /> Back to Subjects
        </Link>
      </div>
    );
  }

  const topics = unit.topics || [];
  const completedTopicsCount = unit.progress?.topics_completed || 0;
  const totalTopicsCount = topics.length;
  const isMasterQuizUnlocked = unit.progress?.master_quiz_unlocked || false;
  const isUnitCompleted = unit.progress?.status === "COMPLETED";

  return (
    <div className="flex flex-col gap-8">
      {/* Breadcrumb & Navigation */}
      <div>
        <Link
          href={`/subjects/${unit.subject_id}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-indigo-600 transition-colors mb-3"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          <span>Back to Subject Units</span>
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700">
                Unit {unit.order_index}
              </span>
              {isUnitCompleted && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-bold text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Unit Completed
                </span>
              )}
            </div>
            <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold text-gray-900">
              {unit.title}
            </h1>
            {unit.description && (
              <p className="mt-1 text-xs sm:text-sm text-gray-600 max-w-2xl">
                {unit.description}
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => {
                setEditTitle(unit.title);
                setEditDesc(unit.description || "");
                setShowEditUnit(true);
              }}
              className="flex items-center gap-1.5 rounded-xl border border-gray-300 bg-white px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 shadow-sm"
            >
              <Pencil className="h-3.5 w-3.5" />
              <span>Edit Unit</span>
            </button>
            <button
              onClick={() => setShowDeleteUnit(true)}
              className="flex items-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-100 shadow-sm"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Delete Unit</span>
            </button>

            {/* Master Unit Quiz Action Button */}
            {totalTopicsCount > 0 && (
              <div>
                {isMasterQuizUnlocked ? (
                  <Link
                    href={`/units/${unit.id}/master-quiz`}
                    className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs sm:text-sm font-bold shadow-md transition-all ${
                      isUnitCompleted
                        ? "bg-emerald-600 text-white hover:bg-emerald-700"
                        : "bg-indigo-600 text-white hover:bg-indigo-700 hover:scale-105"
                    }`}
                  >
                    <Award className="h-4 w-4" />
                    <span>{isUnitCompleted ? "Review Master Quiz" : "Take Master Unit Quiz"}</span>
                  </Link>
                ) : (
                  <div className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-medium text-gray-400 cursor-not-allowed">
                    <Lock className="h-3.5 w-3.5" />
                    <span>Master Quiz Locked</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Resource Upload Section */}
      <div className="flex flex-col gap-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-gray-500">
          Source Material (Source of Truth)
        </h2>
        <DocumentUploader
          unitId={unit.id}
          existingDocument={unit.document}
          onUploadSuccess={handleDocumentUploaded}
        />
      </div>

      {/* Sequential Learning Pathway */}
      {unit.document && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Learning Pathway & Topics</h2>
              <p className="text-xs text-gray-500">
                Topics are extracted from the source in original order. Access any topic at any time and take quizzes to test and track your mastery.
              </p>
            </div>
            {totalTopicsCount > 0 && (
              <span className="text-xs font-semibold text-gray-600">
                {completedTopicsCount} / {totalTopicsCount} Passed
              </span>
            )}
          </div>

          {totalTopicsCount === 0 ? (
            <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-xs text-gray-500">
              Document processing completed, but no topics were extracted. Check document formatting.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {topics.map((topic, idx) => {
                const isPassed = topic.progress_status === "PASSED" || topic.progress_status === "COMPLETED";
                const isInProgress = topic.progress_status === "IN_PROGRESS";

                return (
                  <div
                    key={topic.id}
                    className={`flex items-center justify-between rounded-2xl border p-4 sm:p-5 transition-all ${
                      isPassed
                        ? "border-emerald-200 bg-emerald-50/20"
                        : isInProgress
                        ? "border-indigo-400 bg-indigo-50/20 shadow-sm ring-1 ring-indigo-400"
                        : "border-gray-200 bg-white hover:border-gray-300"
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <div
                        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl font-bold text-xs ${
                          isPassed
                            ? "bg-emerald-100 text-emerald-700"
                            : isInProgress
                            ? "bg-indigo-600 text-white"
                            : "bg-indigo-50 text-indigo-700 border border-indigo-100"
                        }`}
                      >
                        {isPassed ? (
                          <CheckCircle2 className="h-5 w-5" />
                        ) : (
                          <span>{topic.order_index}</span>
                        )}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <h3
                            className={`font-bold text-sm ${
                              isPassed
                                ? "text-emerald-950"
                                : isInProgress
                                ? "text-indigo-950"
                                : "text-gray-900"
                            }`}
                          >
                            {topic.name}
                          </h3>
                          {isPassed && (
                            <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-800">
                              Passed
                            </span>
                          )}
                          {isInProgress && (
                            <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-[10px] font-bold text-indigo-700">
                              In Progress
                            </span>
                          )}
                        </div>

                        {topic.subtopics && topic.subtopics.length > 0 && (
                          <p className="mt-0.5 text-xs text-gray-500">
                            Includes: {topic.subtopics.map((s) => s.name).join(" • ")}
                          </p>
                        )}
                      </div>
                    </div>

                    <div>
                      <Link
                        href={`/topics/${topic.id}`}
                        className={`flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold shadow-sm transition-all hover:scale-105 ${
                          isInProgress
                            ? "bg-indigo-600 text-white hover:bg-indigo-700"
                            : isPassed
                            ? "bg-white border border-emerald-300 text-emerald-800 hover:bg-emerald-50"
                            : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        <span>{isPassed ? "Review Topic" : isInProgress ? "Continue Learning" : "Start Learning"}</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Edit Unit Modal */}
      {showEditUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">Edit Unit</h3>
            <form onSubmit={handleUpdateUnit} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Unit Title
                </label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditUnit(false)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingUnit || !editTitle.trim()}
                  className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {updatingUnit ? "Saving..." : "Update Unit"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Unit Confirmation Modal */}
      {showDeleteUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-base font-bold text-gray-900">Delete Unit?</h3>
            <p className="mt-2 text-xs text-gray-600">
              Are you sure you want to delete <span className="font-semibold text-gray-900">&ldquo;{unit.title}&rdquo;</span>? This will permanently delete its resource document, all topics, and student quiz records.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowDeleteUnit(false)}
                className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteUnit}
                disabled={deletingUnit}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
              >
                {deletingUnit ? "Deleting..." : "Delete Unit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
