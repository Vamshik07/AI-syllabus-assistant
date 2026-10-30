"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { SubjectDetail, UnitDetail, Quiz, QuizAttemptResponse } from "@/types";
import ProgressBar from "@/components/ProgressBar";
import QuizCard from "@/components/QuizCard";
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
  FileText,
  Award,
  Upload,
  Sparkles,
  HelpCircle,
  X,
  AlertCircle,
  Trophy,
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

  // Syllabus Modal state
  const [showSyllabusModal, setShowSyllabusModal] = useState(false);
  const [syllabusTextInput, setSyllabusTextInput] = useState("");
  const [syllabusFile, setSyllabusFile] = useState<File | null>(null);
  const [savingSyllabus, setSavingSyllabus] = useState(false);

  // PYQ Modal state
  const [showPYQModal, setShowPYQModal] = useState(false);
  const [pyqTextInput, setPyqTextInput] = useState("");
  const [pyqFile, setPyqFile] = useState<File | null>(null);
  const [savingPYQ, setSavingPYQ] = useState(false);
  const [pyqSummary, setPyqSummary] = useState<any | null>(null);

  // Final Assessment state
  const [showFinalAssessment, setShowFinalAssessment] = useState(false);
  const [finalQuiz, setFinalQuiz] = useState<Quiz | null>(null);
  const [finalQuizResult, setFinalQuizResult] = useState<QuizAttemptResponse | null>(null);
  const [loadingFinalQuiz, setLoadingFinalQuiz] = useState(false);

  const loadSubject = async () => {
    try {
      setLoading(true);
      const data = await api.getSubject(subjectId);
      setSubject(data);
      if (data.syllabus_text) {
        setSyllabusTextInput(data.syllabus_text);
      }
      setCompanionContext({
        subjectId: data.id,
        subjectName: data.name,
        pageType: "subjects",
      });
      setCatState("IDLE");
      triggerSpeechBubble(`Exploring ${data.name}? Ask me anything or let's conquer our syllabus! 🐱⚔️`, 6000);
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

  // Syllabus Save
  const handleSaveSyllabus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!syllabusTextInput.trim() && !syllabusFile) {
      alert("Please enter syllabus text or choose a syllabus file.");
      return;
    }
    try {
      setSavingSyllabus(true);
      await api.uploadSubjectSyllabus(subjectId, {
        syllabus_text: syllabusTextInput.trim() || undefined,
        file: syllabusFile || undefined,
      });
      setShowSyllabusModal(false);
      setSyllabusFile(null);
      loadSubject();
    } catch (err: any) {
      alert(err.message || "Failed to save syllabus.");
    } finally {
      setSavingSyllabus(false);
    }
  };

  // PYQ Upload
  const handleUploadPYQ = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pyqTextInput.trim() && !pyqFile) {
      alert("Please enter past exam questions or upload a question paper.");
      return;
    }
    try {
      setSavingPYQ(true);
      const res = await api.uploadSubjectPYQ(subjectId, {
        pyq_text: pyqTextInput.trim() || undefined,
        file: pyqFile || undefined,
      });
      setPyqSummary(res);
      setPyqTextInput("");
      setPyqFile(null);
      loadSubject();
    } catch (err: any) {
      alert(err.message || "Failed to analyze PYQs.");
    } finally {
      setSavingPYQ(false);
    }
  };

  // Start Final Assessment
  const handleStartFinalAssessment = async () => {
    setShowFinalAssessment(true);
    setLoadingFinalQuiz(true);
    try {
      const q = await api.generateFinalAssessment(subjectId);
      setFinalQuiz(q);
      if (q) {
        try {
          const latest = await api.getLatestQuizAttempt(q.id);
          setFinalQuizResult(latest || null);
        } catch {
          setFinalQuizResult(null);
        }
      }
    } catch (err: any) {
      alert(err.message || "Failed to generate full-syllabus assessment.");
      setShowFinalAssessment(false);
    } finally {
      setLoadingFinalQuiz(false);
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
  const allUnitsCompleted = totalUnits > 0 && completedUnits === totalUnits;
  const isSubjectMastered = completionPct >= 100;
  const hasSyllabus = !!subject.syllabus_text;
  const hasPYQs = !!subject.pyq_data;

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
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
                {subject.name}
              </h1>
              {isSubjectMastered && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-extrabold text-emerald-800 border border-emerald-300">
                  <Trophy className="h-4 w-4 text-emerald-700" />
                  100% Mastered
                </span>
              )}
            </div>
            {subject.description && (
              <p className="mt-1 text-xs sm:text-sm text-gray-600 max-w-2xl">
                {subject.description}
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Syllabus Upload / View Button */}
            <button
              onClick={() => setShowSyllabusModal(true)}
              className={`flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-bold transition-all shadow-sm ${
                hasSyllabus
                  ? "border border-purple-200 bg-purple-50 text-purple-800 hover:bg-purple-100"
                  : "border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>{hasSyllabus ? "Syllabus Active" : "Upload Syllabus"}</span>
            </button>

            {/* PYQ Papers Button */}
            <button
              onClick={() => setShowPYQModal(true)}
              className={`flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-bold transition-all shadow-sm ${
                hasPYQs
                  ? "border border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100"
                  : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
              }`}
            >
              <Award className="h-3.5 w-3.5" />
              <span>{hasPYQs ? "PYQs Analyzed" : "Upload PYQs"}</span>
            </button>

            <button
              onClick={() => {
                setEditSubjectName(subject.name);
                setEditSubjectDesc(subject.description || "");
                setShowEditSubject(true);
              }}
              className="flex items-center gap-1.5 rounded-xl border border-gray-300 bg-white px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 shadow-sm"
            >
              <Pencil className="h-3.5 w-3.5" />
              <span>Edit</span>
            </button>

            <button
              onClick={() => setShowDeleteSubject(true)}
              className="flex items-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-100 shadow-sm"
            >
              <Trash2 className="h-3.5 w-3.5" />
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
            <h3 className="font-bold text-gray-900 text-sm">Subject Mastery Progress</h3>
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

      {/* 100% Full-Syllabus Master Assessment Section */}
      <div
        className={`rounded-2xl border p-6 shadow-sm transition-all ${
          isSubjectMastered
            ? "border-emerald-300 bg-linear-to-r from-emerald-50 to-teal-50"
            : allUnitsCompleted
            ? "border-indigo-300 bg-linear-to-r from-indigo-50 to-purple-50"
            : "border-gray-200 bg-gray-50/70"
        }`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div
              className={`rounded-2xl p-3 text-white shadow-sm ${
                isSubjectMastered
                  ? "bg-emerald-600"
                  : allUnitsCompleted
                  ? "bg-indigo-600"
                  : "bg-gray-400"
              }`}
            >
              <Trophy className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-gray-900 text-base">
                  Full-Syllabus Comprehensive Assessment
                </h3>
                {isSubjectMastered ? (
                  <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-800">
                    Passed (100% Syllabus Mastery Achieved)
                  </span>
                ) : allUnitsCompleted ? (
                  <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-bold text-indigo-800">
                    Unlocked & Ready
                  </span>
                ) : (
                  <span className="rounded-full bg-gray-200 px-2.5 py-0.5 text-xs font-bold text-gray-600">
                    Locked
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-gray-600 max-w-xl leading-relaxed">
                {isSubjectMastered
                  ? "Congratulations! You completed all units and achieved >= 65% on the comprehensive final exam. Your subject is 100% mastered!"
                  : allUnitsCompleted
                  ? "All unit master quizzes are complete! Take the 12-question full-syllabus exam (passing score >= 65%) to achieve 100% course completion."
                  : `Complete all ${totalUnits} unit master quizzes (${completedUnits}/${totalUnits} completed) to unlock the final comprehensive full-syllabus assessment.`}
              </p>
            </div>
          </div>

          <div>
            {allUnitsCompleted ? (
              <button
                onClick={handleStartFinalAssessment}
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 transition-transform hover:scale-105"
              >
                <Sparkles className="h-4 w-4" />
                <span>{isSubjectMastered ? "Retake Master Exam" : "Take Final Assessment"}</span>
              </button>
            ) : (
              <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-400 bg-white/80 px-3 py-2 rounded-xl border border-gray-200">
                <Lock className="h-4 w-4" />
                <span>Pass all units to unlock</span>
              </div>
            )}
          </div>
        </div>
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
                          percentage={roundPercentage(topicsCompleted, totalTopics)}
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

      {/* Syllabus Modal */}
      {showSyllabusModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl border border-gray-200">
            <div className="flex items-center justify-between border-b pb-3 mb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Official Syllabus Setup</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  The syllabus establishes canonical topic names. Uploaded study resources will map into these topics.
                </p>
              </div>
              <button
                onClick={() => setShowSyllabusModal(false)}
                className="rounded-lg p-1 text-gray-400 hover:bg-gray-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSaveSyllabus} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Upload Syllabus File (PDF, DOCX, TXT)
                </label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={(e) => setSyllabusFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                />
              </div>

              <div className="text-center text-xs text-gray-400 font-semibold">— OR PASTE TEXT —</div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Syllabus Outline / Text
                </label>
                <textarea
                  rows={6}
                  placeholder="Paste unit syllabus titles and topic names here..."
                  value={syllabusTextInput}
                  onChange={(e) => setSyllabusTextInput(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 p-3 text-xs font-mono focus:border-indigo-600 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSyllabusModal(false)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingSyllabus}
                  className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {savingSyllabus ? "Saving..." : "Save Canonical Syllabus"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PYQ Papers Modal */}
      {showPYQModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl border border-gray-200">
            <div className="flex items-center justify-between border-b pb-3 mb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Upload Past Exam Papers (PYQs)</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  AI extracts questions and matches them against topics to highlight high-probability exam topics.
                </p>
              </div>
              <button
                onClick={() => setShowPYQModal(false)}
                className="rounded-lg p-1 text-gray-400 hover:bg-gray-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {pyqSummary && (
              <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 mb-4 text-xs text-emerald-900">
                <div className="font-bold mb-1">PYQ Analysis Completed!</div>
                <div>Extracted: {pyqSummary.extracted_questions_count} questions</div>
                <div>Matched to Topics: {pyqSummary.matched_topics_count} topic matches</div>
              </div>
            )}

            <form onSubmit={handleUploadPYQ} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Upload Question Paper (PDF, DOCX, TXT)
                </label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={(e) => setPyqFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-amber-50 file:text-amber-800 hover:file:bg-amber-100"
                />
              </div>

              <div className="text-center text-xs text-gray-400 font-semibold">— OR PASTE QUESTIONS —</div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Exam Questions Text
                </label>
                <textarea
                  rows={5}
                  placeholder="e.g. 1. What are the key steps in the planning process? (7 Marks)&#10;2. Define characteristics of effective plans..."
                  value={pyqTextInput}
                  onChange={(e) => setPyqTextInput(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 p-3 text-xs font-mono focus:border-amber-600 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPYQModal(false)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={savingPYQ}
                  className="rounded-xl bg-amber-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-amber-700 disabled:opacity-50"
                >
                  {savingPYQ ? "Analyzing Questions..." : "Analyze PYQs"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Full-Syllabus Final Assessment Modal */}
      {showFinalAssessment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-4xl rounded-3xl bg-white p-6 sm:p-8 shadow-2xl border border-gray-200 my-8">
            <div className="flex items-center justify-between border-b border-gray-200 pb-4 mb-6">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-extrabold text-indigo-700">
                    Full Syllabus Exam
                  </span>
                  <span className="text-xs text-gray-500 font-semibold">Passing: &ge; 65%</span>
                </div>
                <h2 className="text-xl font-extrabold text-gray-900 mt-1">
                  {subject.name} — Comprehensive Master Assessment
                </h2>
              </div>
              <button
                onClick={() => {
                  setShowFinalAssessment(false);
                  loadSubject();
                }}
                className="rounded-xl p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {loadingFinalQuiz ? (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent mb-3" />
                <p className="font-semibold text-gray-800 text-sm">Synthesizing full-syllabus questions...</p>
                <p className="text-xs text-gray-500 mt-1">
                  Selecting balanced questions across all {totalUnits} subject units.
                </p>
              </div>
            ) : finalQuiz ? (
              <QuizCard
                quiz={finalQuiz}
                topicTitle={`${subject.name} Comprehensive Assessment`}
                initialResult={finalQuizResult}
                onSuccess={(res) => {
                  setFinalQuizResult(res);
                  loadSubject();
                }}
                onRetry={() => setFinalQuizResult(null)}
                onFreshQuestions={handleStartFinalAssessment}
              />
            ) : null}
          </div>
        </div>
      )}

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
