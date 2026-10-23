"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { SubjectDetail, UnitDetail } from "@/types";
import ProgressBar from "@/components/ProgressBar";
import {
  Layers,
  Plus,
  ArrowRight,
  FileCheck2,
  FileQuestion,
  ChevronLeft,
  CheckCircle2,
  Lock,
  Pencil,
  Trash2,
} from "lucide-react";
import { useCatCompanion } from "@/context/CatCompanionContext";

export default function SubjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const subjectId = params.id as string;

  const [subject, setSubject] = useState<SubjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { setCatState, triggerSpeechBubble, setCompanionContext } = useCatCompanion();

  // Add unit state
  const [showAddUnit, setShowAddUnit] = useState(false);
  const [unitTitle, setUnitTitle] = useState("");
  const [unitDesc, setUnitDesc] = useState("");
  const [addingUnit, setAddingUnit] = useState(false);

  // Edit Subject state
  const [showEditSubject, setShowEditSubject] = useState(false);
  const [editSubjectName, setEditSubjectName] = useState("");
  const [editSubjectDesc, setEditSubjectDesc] = useState("");
  const [updatingSubject, setUpdatingSubject] = useState(false);

  // Delete Subject state
  const [showDeleteSubject, setShowDeleteSubject] = useState(false);
  const [deletingSubject, setDeletingSubject] = useState(false);

  // Edit Unit state
  const [editingUnit, setEditingUnit] = useState<UnitDetail | null>(null);
  const [editUnitTitle, setEditUnitTitle] = useState("");
  const [editUnitDesc, setEditUnitDesc] = useState("");
  const [updatingUnit, setUpdatingUnit] = useState(false);

  // Delete Unit state
  const [deletingUnit, setDeletingUnit] = useState<UnitDetail | null>(null);
  const [deletingUnitLoading, setDeletingUnitLoading] = useState(false);

  const loadSubject = async () => {
    try {
      setLoading(true);
      const data = await api.getSubject(subjectId);
      setSubject(data);
      setCompanionContext({
        subjectId: data.id,
        subjectName: data.name,
        pageType: "subjects",
      });
      setCatState("IDLE");
      triggerSpeechBubble(`Exploring ${data.name}? Ask me anything or let's pick a unit to conquer! 🐱⚔️`, 6000);
    } catch (err: any) {
      setError(err.message || "Failed to load subject details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (subjectId) {
      loadSubject();
    }
  }, [subjectId]);

  const handleAddUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!unitTitle.trim() || !subject) return;

    try {
      setAddingUnit(true);
      const nextOrder = (subject.units?.length || 0) + 1;
      await api.createUnit(subject.id, {
        title: unitTitle.trim(),
        order_index: nextOrder,
        description: unitDesc.trim() || undefined,
      });
      setUnitTitle("");
      setUnitDesc("");
      setShowAddUnit(false);
      loadSubject();
    } catch (err: any) {
      alert(err.message || "Failed to add unit.");
    } finally {
      setAddingUnit(false);
    }
  };

  const handleUpdateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editSubjectName.trim()) return;
    try {
      setUpdatingSubject(true);
      await api.updateSubject(subjectId, {
        name: editSubjectName.trim(),
        description: editSubjectDesc.trim() || undefined,
      });
      setShowEditSubject(false);
      loadSubject();
    } catch (err: any) {
      alert(err.message || "Failed to update subject.");
    } finally {
      setUpdatingSubject(false);
    }
  };

  const handleDeleteSubject = async () => {
    try {
      setDeletingSubject(true);
      await api.deleteSubject(subjectId);
      router.push("/subjects");
    } catch (err: any) {
      alert(err.message || "Failed to delete subject.");
      setDeletingSubject(false);
    }
  };

  const handleUpdateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUnit || !editUnitTitle.trim()) return;
    try {
      setUpdatingUnit(true);
      await api.updateUnit(editingUnit.id, {
        title: editUnitTitle.trim(),
        description: editUnitDesc.trim() || undefined,
      });
      setEditingUnit(null);
      loadSubject();
    } catch (err: any) {
      alert(err.message || "Failed to update unit.");
    } finally {
      setUpdatingUnit(false);
    }
  };

  const handleDeleteUnit = async () => {
    if (!deletingUnit) return;
    try {
      setDeletingUnitLoading(true);
      await api.deleteUnit(deletingUnit.id);
      setDeletingUnit(null);
      loadSubject();
    } catch (err: any) {
      alert(err.message || "Failed to delete unit.");
    } finally {
      setDeletingUnitLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-6 animate-pulse">
        <div className="h-8 w-48 bg-gray-200 rounded-lg" />
        <div className="h-32 bg-gray-100 rounded-2xl border border-gray-200" />
        <div className="h-64 bg-gray-100 rounded-2xl border border-gray-200" />
      </div>
    );
  }

  if (error || !subject) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-sm text-red-700">
        <p className="font-semibold">{error || "Subject not found."}</p>
        <Link
          href="/subjects"
          className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 underline"
        >
          <ChevronLeft className="h-4 w-4" /> Back to Subjects
        </Link>
      </div>
    );
  }

  const completionPct = subject.progress?.completion_percentage || 0;
  const completedUnits = subject.progress?.units_completed || 0;
  const totalUnits = subject.units?.length || 0;

  return (
    <div className="flex flex-col gap-8">
      {/* Breadcrumb & Header */}
      <div>
        <Link
          href="/subjects"
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-indigo-600 transition-colors mb-3"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          <span>Back to Subjects</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
              {subject.name}
            </h1>
            {subject.description && (
              <p className="mt-1 text-xs sm:text-sm text-gray-600 max-w-2xl">
                {subject.description}
              </p>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => {
                setEditSubjectName(subject.name);
                setEditSubjectDesc(subject.description || "");
                setShowEditSubject(true);
              }}
              className="flex items-center gap-1.5 rounded-xl border border-gray-300 bg-white px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 shadow-sm"
            >
              <Pencil className="h-3.5 w-3.5" />
              <span>Edit Subject</span>
            </button>
            <button
              onClick={() => setShowDeleteSubject(true)}
              className="flex items-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-100 shadow-sm"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Delete Subject</span>
            </button>
            <button
              onClick={() => setShowAddUnit(true)}
              className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4" />
              <span>Add Unit</span>
            </button>
          </div>
        </div>
      </div>

      {/* Subject Progress Card */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-bold text-gray-900 text-sm">Subject Mastery</h3>
            <p className="text-xs text-gray-500">
              {completedUnits} of {totalUnits} units fully completed (Master Quiz passed)
            </p>
          </div>
          <span className="rounded-full bg-indigo-50 px-3 py-1 font-mono text-xs font-bold text-indigo-700">
            {completionPct}% Complete
          </span>
        </div>
        <ProgressBar percentage={completionPct} showLabel={false} size="md" />
      </div>

      {/* Units List */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Units in this Subject</h2>
          <span className="text-xs text-gray-500">{totalUnits} Units</span>
        </div>

        {totalUnits === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-gray-300 bg-white p-12 text-center">
            <Layers className="h-10 w-10 text-gray-400 mx-auto mb-2" />
            <h3 className="font-bold text-gray-800 text-sm">No units in this subject yet</h3>
            <p className="mt-1 text-xs text-gray-500 max-w-sm mx-auto">
              Add your first unit (e.g. &ldquo;Unit 1: Process Management&rdquo;) and upload its educational source document.
            </p>
            <button
              onClick={() => setShowAddUnit(true)}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4" />
              Add Unit 1
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {subject.units?.map((unit: UnitDetail) => {
              const hasDoc = !!unit.document;
              const isUnitCompleted = unit.progress?.status === "COMPLETED";
              const topicsCompleted = unit.progress?.topics_completed || 0;
              const totalTopics = unit.progress?.total_topics || unit.topics?.length || 0;

              return (
                <Link
                  key={unit.id}
                  href={`/units/${unit.id}`}
                  className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md"
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl font-bold text-sm ${
                        isUnitCompleted
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-indigo-50 text-indigo-700"
                      }`}
                    >
                      {isUnitCompleted ? (
                        <CheckCircle2 className="h-6 w-6 text-emerald-600" />
                      ) : (
                        `U${unit.order_index}`
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-gray-900 group-hover:text-indigo-600 transition-colors">
                          {unit.title}
                        </h3>
                        {isUnitCompleted && (
                          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                            Unit Completed
                          </span>
                        )}
                      </div>
                      {unit.description && (
                        <p className="mt-1 line-clamp-1 text-xs text-gray-500">
                          {unit.description}
                        </p>
                      )}
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                        {hasDoc ? (
                          <span className="inline-flex items-center gap-1 font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px]">
                            <FileCheck2 className="h-3.5 w-3.5" />
                            {unit.document?.file_type}: {unit.document?.file_name}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded text-[11px]">
                            <FileQuestion className="h-3.5 w-3.5" />
                            No document uploaded yet
                          </span>
                        )}

                        {totalTopics > 0 && (
                          <span>
                            • {topicsCompleted} / {totalTopics} topics passed
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-3 border-t sm:border-t-0 pt-3 sm:pt-0">
                    {totalTopics > 0 && (
                      <div className="w-24 hidden sm:block">
                        <ProgressBar
                          percentage={
                            roundPercentage(topicsCompleted, totalTopics)
                          }
                          size="sm"
                          showLabel={false}
                        />
                      </div>
                    )}
                    <span className="flex items-center gap-1 text-xs font-semibold text-indigo-600 group-hover:translate-x-1 transition-transform">
                      Open Unit
                      <ArrowRight className="h-4 w-4" />
                    </span>

                    {/* Unit actions */}
                    <div className="flex items-center gap-1 pl-2 border-l border-gray-100">
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setEditingUnit(unit);
                          setEditUnitTitle(unit.title);
                          setEditUnitDesc(unit.description || "");
                        }}
                        title="Edit Unit"
                        className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setDeletingUnit(unit);
                        }}
                        title="Delete Unit"
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Unit Modal */}
      {showAddUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">Add Unit to {subject.name}</h3>
            <form onSubmit={handleAddUnit} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Unit Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Unit 1: Introduction to Network Models"
                  value={unitTitle}
                  onChange={(e) => setUnitTitle(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Syllabus overview or key focus areas"
                  value={unitDesc}
                  onChange={(e) => setUnitDesc(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddUnit(false)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addingUnit || !unitTitle.trim()}
                  className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {addingUnit ? "Adding..." : "Add Unit"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Subject Modal */}
      {showEditSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">Edit Subject</h3>
            <form onSubmit={handleUpdateSubject} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Subject Name
                </label>
                <input
                  type="text"
                  required
                  value={editSubjectName}
                  onChange={(e) => setEditSubjectName(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={editSubjectDesc}
                  onChange={(e) => setEditSubjectDesc(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditSubject(false)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingSubject || !editSubjectName.trim()}
                  className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {updatingSubject ? "Saving..." : "Update Subject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Subject Confirmation Modal */}
      {showDeleteSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-base font-bold text-gray-900">Delete Subject?</h3>
            <p className="mt-2 text-xs text-gray-600">
              Are you sure you want to delete <span className="font-semibold text-gray-900">&ldquo;{subject.name}&rdquo;</span>? This will permanently delete all units, documents, quizzes, and learning progress in this subject.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowDeleteSubject(false)}
                className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteSubject}
                disabled={deletingSubject}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
              >
                {deletingSubject ? "Deleting..." : "Delete Permanently"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Unit Modal */}
      {editingUnit && (
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
                  value={editUnitTitle}
                  onChange={(e) => setEditUnitTitle(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={editUnitDesc}
                  onChange={(e) => setEditUnitDesc(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingUnit(null)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingUnit || !editUnitTitle.trim()}
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
      {deletingUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-base font-bold text-gray-900">Delete Unit?</h3>
            <p className="mt-2 text-xs text-gray-600">
              Are you sure you want to delete <span className="font-semibold text-gray-900">&ldquo;{deletingUnit.title}&rdquo;</span>? This will permanently delete its resource document, all topics, and student quiz records.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeletingUnit(null)}
                className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteUnit}
                disabled={deletingUnitLoading}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
              >
                {deletingUnitLoading ? "Deleting..." : "Delete Unit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function roundPercentage(completed: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((completed / total) * 100);
}
