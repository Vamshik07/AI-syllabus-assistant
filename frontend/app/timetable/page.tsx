"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  Clock3,
  Sparkles,
  BookOpen,
  CheckCircle2,
  Lock,
  LogIn,
  UserPlus,
  Printer,
  ChevronRight,
  ListChecks,
  AlertCircle,
  AlertTriangle,
  RotateCcw,
  Star,
  Flame,
  CheckSquare,
  Square,
  Filter,
  Layers,
  ArrowRight,
  GraduationCap,
  ShieldAlert,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "@/lib/api";
import { Subject, StudyPlan, StudyPlanItem, TopicForPlan, RoadmapDay } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { useCatCompanion } from "@/context/CatCompanionContext";

const today = new Date().toISOString().slice(0, 10);

function addDays(baseDate: string, days: number): string {
  const d = new Date(baseDate);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hrs}h ${mins}m` : `${hrs}h`;
}

export default function TimetablePage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { setCatState, triggerSpeechBubble, setCompanionContext } = useCatCompanion();

  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(addDays(today, 9)); // 10 days default
  const [dailyHours, setDailyHours] = useState("2");

  // Advanced topic customization state (default: all topics included)
  const [availableTopics, setAvailableTopics] = useState<TopicForPlan[]>([]);
  const [selectedTopicIds, setSelectedTopicIds] = useState<string[]>([]);
  const [showTopicFilter, setShowTopicFilter] = useState(false);

  useEffect(() => {
    setCompanionContext({ pageType: "timetable" });
    setCatState("ROADMAP");
    triggerSpeechBubble("Today's quest awaits on your roadmap! Let's level up together! 🐱📜", 7000, "ROADMAP");
  }, [setCompanionContext, setCatState, triggerSpeechBubble]);

  // Active Roadmap state
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Filter roadmap items
  const [activeFilter, setActiveFilter] = useState<"ALL" | "HIGH_PRIORITY" | "WEAK" | "REVISION" | "COMPLETED">("ALL");

  // Expanded details per item (item_id -> boolean)
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

  // Completed checklist tasks state (taskKey -> boolean)
  const [completedTasks, setCompletedTasks] = useState<Record<string, boolean>>({});

  // Completed items state (itemId -> boolean)
  const [completedItems, setCompletedItems] = useState<Record<string, boolean>>({});

  // Load user subjects
  useEffect(() => {
    if (isAuthenticated) {
      api
        .getSubjects()
        .then((items) => {
          setSubjects(items);
          if (items.length > 0) setSubjectId(items[0].id);
        })
        .catch((err) => setError(err.message));
    }
  }, [isAuthenticated]);

  // Load topics and existing saved roadmap when subject changes
  useEffect(() => {
    if (subjectId) {
      // 1. Load topics for this subject
      api
        .getTopicsForPlan(subjectId)
        .then((topics) => {
          setAvailableTopics(topics);
          setSelectedTopicIds(topics.map((t) => t.topic_id));
        })
        .catch((err) => {
          console.error("Failed to load topics:", err);
        });

      // 2. Load existing active roadmap if one was previously saved
      api
        .getStudyPlan(subjectId)
        .then((savedPlan) => {
          if (savedPlan && savedPlan.schedule) {
            setPlan(savedPlan);
            if (savedPlan.start_date) setStartDate(savedPlan.start_date);
            if (savedPlan.end_date) setEndDate(savedPlan.end_date);
            if (savedPlan.daily_hours) setDailyHours(savedPlan.daily_hours.toString());
          }
        })
        .catch(() => {
          // No saved plan yet, which is expected for new subjects
        });
    }
  }, [subjectId]);

  const applyPreset = (days: number) => {
    setStartDate(today);
    setEndDate(addDays(today, days - 1));
  };

  const totalDays = useMemo(() => {
    const s = new Date(startDate);
    const e = new Date(endDate);
    const diff = Math.floor((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    return Math.max(1, isNaN(diff) ? 1 : diff);
  }, [startDate, endDate]);

  const totalAvailableStudyHours = useMemo(() => {
    return totalDays * Number(dailyHours || 1);
  }, [totalDays, dailyHours]);

  const generatePlan = async (event?: FormEvent) => {
    if (event) event.preventDefault();
    if (!subjectId) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.createStudyPlan(subjectId, {
        start_date: startDate,
        end_date: endDate,
        daily_hours: Number(dailyHours),
        material_preference: "auto",
        selected_topic_ids: selectedTopicIds.length > 0 && selectedTopicIds.length < availableTopics.length
          ? selectedTopicIds
          : undefined,
      });
      setPlan(result);
    } catch (err: any) {
      setError(
        err.message ||
          "Could not generate roadmap. Ensure your subject has at least one processed unit."
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleTask = (taskKey: string) => {
    setCompletedTasks((prev) => ({
      ...prev,
      [taskKey]: !prev[taskKey],
    }));
  };

  const toggleItemDone = (key: string) => {
    setCompletedItems((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const toggleExpand = (itemId: string) => {
    setExpandedItems((prev) => ({
      ...prev,
      [itemId]: !prev[itemId],
    }));
  };

  const toggleTopicSelection = (topicId: string) => {
    setSelectedTopicIds((prev) =>
      prev.includes(topicId)
        ? prev.filter((id) => id !== topicId)
        : [...prev, topicId]
    );
  };

  // Group roadmap by days
  const dailyRoadmap = useMemo(() => {
    if (!plan) return [];
    if (plan.daily_schedule && plan.daily_schedule.length > 0) {
      return plan.daily_schedule;
    }
    // Fallback: group flat schedule by date
    const grouped = new Map<string, StudyPlanItem[]>();
    plan.schedule.forEach((item) => {
      const dateKey = item.date || today;
      grouped.set(dateKey, [...(grouped.get(dateKey) || []), item]);
    });
    return Array.from(grouped.entries()).map(([date, items], idx) => ({
      day_number: items[0]?.day_number || idx + 1,
      date,
      available_hours: plan.daily_hours,
      allocated_hours: roundHours(items.reduce((acc, it) => acc + (it.allocated_minutes || it.study_minutes || 0), 0) / 60),
      allocated_minutes: items.reduce((acc, it) => acc + (it.allocated_minutes || it.study_minutes || 0), 0),
      remaining_minutes: Math.max(0, (plan.daily_hours * 60) - items.reduce((acc, it) => acc + (it.allocated_minutes || it.study_minutes || 0), 0)),
      items,
    }));
  }, [plan]);

  function roundHours(h: number): number {
    return Math.round(h * 10) / 10;
  }

  // Filter items in daily roadmap
  const filteredDailyRoadmap = useMemo(() => {
    if (activeFilter === "ALL") return dailyRoadmap;

    return dailyRoadmap.map((day) => {
      const filteredItems = day.items.filter((item) => {
        const isHigh = item.priority === "HIGH" || item.rank === 1;
        const isWeak = item.status === "NEEDS_REVISION";
        const isCompleted = item.status === "COMPLETED" || !!completedItems[item.topic_id];
        const isRevision = item.item_type === "REVISION" || item.item_type === "PRACTICE" || item.item_type === "ASSESSMENT";

        if (activeFilter === "HIGH_PRIORITY") return isHigh;
        if (activeFilter === "WEAK") return isWeak;
        if (activeFilter === "REVISION") return isRevision;
        if (activeFilter === "COMPLETED") return isCompleted;
        return true;
      });
      return { ...day, items: filteredItems };
    }).filter((day) => day.items.length > 0);
  }, [dailyRoadmap, activeFilter, completedItems]);

  if (authLoading) {
    return (
      <div className="flex justify-center items-center py-20 text-sm text-gray-500">
        Loading preparation roadmap engine...
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="rounded-3xl border border-indigo-100 bg-white p-10 text-center shadow-lg shadow-indigo-50/50 max-w-lg mx-auto my-12">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 mx-auto mb-4">
          <Lock className="h-7 w-7" />
        </div>
        <h2 className="text-xl font-bold text-gray-900">
          Sign In to Access Preparation Roadmap
        </h2>
        <p className="mt-2 text-xs text-gray-500 leading-relaxed">
          Create an exam-focused, mathematically valid study roadmap.
          Calculates workload-proportional time, prioritizes heavier topics, and schedules dedicated revision and assessment.
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
    );
  }

  return (
    <div className="flex flex-col gap-8 pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600">
            <CalendarDays className="h-5 w-5" />
            <span className="text-xs font-bold uppercase tracking-wider">
              Study Planning Engine
            </span>
          </div>
          <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold text-gray-900">
            Priority-Based Study Roadmap
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-gray-500 max-w-3xl">
            Answers: <strong>What to study</strong>, <strong>When to study</strong>, <strong>How long</strong>, and <strong>When to revise & test</strong>.
            Strict daily study-hour limits with workload-proportional planning. Click any topic to open its learning page.
          </p>
        </div>

        {plan && (
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-xs font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors self-start sm:self-auto"
          >
            <Printer className="h-4 w-4 text-gray-500" />
            <span>Print Roadmap</span>
          </button>
        )}
      </div>

      {/* Input Configuration Card */}
      <form
        onSubmit={generatePlan}
        className="rounded-3xl border border-gray-200 bg-white p-6 sm:p-8 shadow-sm space-y-5"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
          <h3 className="text-sm font-bold text-gray-900">
            Preparation Inputs & Daily Time Limit
          </h3>

          <div className="flex items-center gap-1.5 text-xs font-medium text-gray-500 flex-wrap">
            <span>Quick Presets:</span>
            <button
              type="button"
              onClick={() => applyPreset(3)}
              className="rounded-lg bg-gray-100 px-2 py-1 hover:bg-indigo-50 hover:text-indigo-600 transition-colors text-[11px]"
            >
              📅 3-Day Sprint
            </button>
            <button
              type="button"
              onClick={() => applyPreset(5)}
              className="rounded-lg bg-gray-100 px-2 py-1 hover:bg-indigo-50 hover:text-indigo-600 transition-colors text-[11px]"
            >
              ⚡ 5-Day Fast-Track
            </button>
            <button
              type="button"
              onClick={() => applyPreset(10)}
              className="rounded-lg bg-indigo-50 text-indigo-700 font-bold px-2 py-1 border border-indigo-200 text-[11px]"
            >
              🎯 10-Day Plan (20h)
            </button>
            <button
              type="button"
              onClick={() => applyPreset(14)}
              className="rounded-lg bg-gray-100 px-2 py-1 hover:bg-indigo-50 hover:text-indigo-600 transition-colors text-[11px]"
            >
              📚 14-Day Mastery
            </button>
          </div>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {/* Target Subject */}
          <div className="sm:col-span-2 lg:col-span-1">
            <label className="block text-xs font-bold text-gray-700 mb-1.5">
              Target Subject
            </label>
            <select
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              className="w-full rounded-xl border border-gray-300 p-2.5 text-xs sm:text-sm font-medium focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600"
            >
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1.5">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full rounded-xl border border-gray-300 p-2.5 text-xs sm:text-sm font-medium focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600"
              required
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1.5">
              End Date ({totalDays} Days)
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full rounded-xl border border-gray-300 p-2.5 text-xs sm:text-sm font-medium focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600"
              required
            />
          </div>

          {/* Daily Study Hours (Hard Limit) */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-gray-700">
                Daily Limit (Hard Limit)
              </label>
              <span className="text-[10px] font-semibold text-rose-600 bg-rose-50 px-1.5 py-0.2 rounded">
                Never exceeded
              </span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0.5"
                max="16"
                step="0.5"
                value={dailyHours}
                onChange={(e) => setDailyHours(e.target.value)}
                className="w-full rounded-xl border border-gray-300 p-2.5 text-xs sm:text-sm font-medium focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600"
                required
              />
              <span className="text-xs font-semibold text-gray-500 whitespace-nowrap">
                hrs/day
              </span>
            </div>
          </div>
        </div>

        {/* Math & Capacity Preview */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-gray-100 text-xs text-gray-600">
          <div className="flex items-center gap-2 flex-wrap">
            <span>
              Total Available Capacity: <strong>{totalDays} days × {dailyHours} hrs/day = {totalAvailableStudyHours.toFixed(1)} Hours Maximum</strong>
            </span>
            <span className="text-gray-300 hidden sm:inline">•</span>
            <span>
              Syllabus Topics: <strong>{availableTopics.length} topics</strong>
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => setShowTopicFilter(!showTopicFilter)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-indigo-600 transition-colors"
            >
              <Filter className="h-3.5 w-3.5" />
              <span>{showTopicFilter ? "Hide Custom Filter" : "Filter Topics (Optional)"}</span>
              {showTopicFilter ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>

            <button
              type="submit"
              disabled={loading || subjects.length === 0}
              className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 disabled:opacity-50 transition-all hover:scale-[1.01]"
            >
              {plan ? <RotateCcw className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
              <span>{loading ? "Calculating Roadmap..." : plan ? "Recalculate Roadmap" : "Generate Study Roadmap"}</span>
            </button>
          </div>
        </div>

        {/* Optional Collapsible Topic Filter */}
        {showTopicFilter && availableTopics.length > 0 && (
          <div className="pt-3 border-t border-gray-100">
            <div className="flex items-center justify-between text-xs font-bold text-gray-700 mb-2">
              <span>Included Topics ({selectedTopicIds.length} of {availableTopics.length}):</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedTopicIds(availableTopics.map(t => t.topic_id))}
                  className="text-indigo-600 hover:underline text-[11px]"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedTopicIds([])}
                  className="text-gray-500 hover:underline text-[11px]"
                >
                  Deselect All
                </button>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 max-h-48 overflow-y-auto pr-1">
              {availableTopics.map((topic) => {
                const isSelected = selectedTopicIds.includes(topic.topic_id);
                return (
                  <label
                    key={topic.topic_id}
                    onClick={() => toggleTopicSelection(topic.topic_id)}
                    className={`flex items-start gap-2 p-2 rounded-xl border text-xs cursor-pointer select-none transition-all ${
                      isSelected
                        ? "bg-indigo-50/50 border-indigo-200 text-indigo-950 font-medium"
                        : "bg-gray-50 border-gray-200 text-gray-400 hover:bg-white"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="rounded text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5 mt-0.5"
                    />
                    <span className="truncate">{topic.topic_name}</span>
                  </label>
                );
              })}
            </div>
          </div>
        )}
      </form>

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-xs text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
          <div>
            <p className="font-bold">Roadmap Generation Error</p>
            <p className="mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* SUMMARY BANNER */}
      {plan && (
        <div className="rounded-3xl border border-indigo-100 bg-white p-6 sm:p-7 shadow-sm space-y-5">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">
                  Roadmap for {plan.subject_name}
                </span>
                <span className="rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200 px-2.5 py-0.5 text-[10px] font-bold">
                  {plan.days} Days Schedule
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-gray-900 mt-1">
                {plan.days}-Day Study Roadmap ({plan.daily_hours}h / day)
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Mathematical validation: Daily hours are capped strictly at {plan.daily_hours}h. Workload allocated proportionally.
              </p>
            </div>

            {/* Quick Metrics Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 self-stretch md:self-auto">
              <div className="rounded-2xl border border-gray-100 bg-slate-50/70 p-3 text-center">
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Available</p>
                <p className="text-base font-extrabold text-gray-900 mt-0.5">{plan.total_available_hours || (plan.days * plan.daily_hours)}h</p>
              </div>

              <div className="rounded-2xl border border-indigo-100 bg-indigo-50/50 p-3 text-center">
                <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">Scheduled</p>
                <p className="text-base font-extrabold text-indigo-950 mt-0.5">{plan.total_scheduled_hours || plan.total_hours}h</p>
              </div>

              <div className="rounded-2xl border border-gray-100 bg-slate-50/70 p-3 text-center">
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Revision</p>
                <p className="text-base font-extrabold text-purple-700 mt-0.5">{plan.revision_hours || 0}h</p>
              </div>

              <div className="rounded-2xl border border-gray-100 bg-slate-50/70 p-3 text-center">
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Buffer</p>
                <p className="text-base font-extrabold text-emerald-700 mt-0.5">{plan.buffer_hours || 0}h</p>
              </div>
            </div>
          </div>

          {/* Shortfall Alert if Applicable */}
          {plan.has_shortfall && (
            <div className="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-xs text-amber-900">
              <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 mt-0.5" />
              <div>
                <p className="font-bold">Preparation Capacity Notice</p>
                <p className="mt-0.5 leading-relaxed">{plan.shortfall_message}</p>
                <p className="mt-1 font-semibold text-amber-800">
                  Tip: Consider increasing daily hours or extending the preparation period by {plan.shortfall_hours} hours for full coverage.
                </p>
              </div>
            </div>
          )}

          {/* Rule 26: 65% Syllabus Completion Rule Reminder */}
          <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-3.5 flex items-start gap-3 text-xs text-indigo-900">
            <GraduationCap className="h-4 w-4 text-indigo-600 shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-bold">Syllabus Completion Requirement (65% Rule): </span>
              Completing topic reading does not automatically award 100% syllabus completion.
              You must pass the <strong>Full-Syllabus Master Assessment</strong> with a score of <strong>≥ 65%</strong> on Day {plan.days}.
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center justify-between border-t border-gray-100 pt-3 flex-wrap gap-2">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs font-bold text-gray-500 mr-1">Filter View:</span>

              <button
                type="button"
                onClick={() => setActiveFilter("ALL")}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeFilter === "ALL"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                All Days ({dailyRoadmap.length})
              </button>

              <button
                type="button"
                onClick={() => setActiveFilter("HIGH_PRIORITY")}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeFilter === "HIGH_PRIORITY"
                    ? "bg-rose-600 text-white shadow-xs"
                    : "bg-rose-50 text-rose-800 hover:bg-rose-100"
                }`}
              >
                🔥 High Priority
              </button>

              <button
                type="button"
                onClick={() => setActiveFilter("REVISION")}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeFilter === "REVISION"
                    ? "bg-purple-600 text-white shadow-xs"
                    : "bg-purple-50 text-purple-800 hover:bg-purple-100"
                }`}
              >
                🔄 Revision & Assessments
              </button>

              <button
                type="button"
                onClick={() => setActiveFilter("WEAK")}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeFilter === "WEAK"
                    ? "bg-amber-600 text-white shadow-xs"
                    : "bg-amber-50 text-amber-800 hover:bg-amber-100"
                }`}
              >
                ⚠️ Needs Revision
              </button>
            </div>

            <div className="text-xs text-gray-500">
              Showing <strong>{filteredDailyRoadmap.length}</strong> of {dailyRoadmap.length} days
            </div>
          </div>
        </div>
      )}

      {/* PRIMARY VIEW: DAY-BY-DAY ROADMAP (DAY -> TOPIC -> TIME) */}
      {plan && (
        <div className="flex flex-col gap-6">
          {filteredDailyRoadmap.map((day) => {
            const formattedDate = new Date(`${day.date}T00:00:00`).toLocaleDateString(
              undefined,
              {
                weekday: "long",
                month: "short",
                day: "numeric",
              }
            );

            return (
              <section
                key={day.date}
                className="rounded-3xl border border-gray-200 bg-white p-5 sm:p-7 shadow-xs hover:border-gray-300 transition-all"
              >
                {/* Day Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-gray-100 pb-3.5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600 text-white font-extrabold text-sm shadow-sm shadow-indigo-100">
                      D{day.day_number}
                    </div>
                    <div>
                      <h3 className="text-base sm:text-lg font-extrabold text-gray-900">
                        Day {day.day_number} • {formattedDate}
                      </h3>
                      <p className="text-xs text-gray-500">
                        {day.items.length} {day.items.length === 1 ? "session" : "sessions"} planned • Available: {day.available_hours}h
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    <span className="rounded-xl bg-slate-100 border border-slate-200 px-3 py-1.5 text-xs font-bold text-gray-700">
                      Total Time: {formatMinutes(day.allocated_minutes)}
                    </span>
                    {day.remaining_minutes > 0 && (
                      <span className="rounded-xl bg-emerald-50 border border-emerald-200 px-2.5 py-1.5 text-[11px] font-bold text-emerald-800">
                        +{formatMinutes(day.remaining_minutes)} buffer
                      </span>
                    )}
                  </div>
                </div>

                {/* Day Items List (WHAT SHOULD I STUDY? HOW MUCH TIME?) */}
                <div className="mt-5 flex flex-col gap-3.5">
                  {day.items.map((item, itIdx) => {
                    const isDone = !!completedItems[item.topic_id];
                    const isHigh = item.priority === "HIGH" || item.rank === 1;
                    const isMedium = item.priority === "MEDIUM" || item.rank === 2;
                    const isRevision = item.item_type === "REVISION" || item.item_type === "PRACTICE";
                    const isAssessment = item.item_type === "ASSESSMENT";
                    const isWeak = item.status === "NEEDS_REVISION";
                    const isExpanded = !!expandedItems[item.topic_id];

                    return (
                      <div
                        key={`${item.topic_id}-${itIdx}`}
                        className={`rounded-2xl border transition-all p-4 sm:p-5 ${
                          isDone
                            ? "bg-emerald-50/30 border-emerald-200 opacity-90"
                            : isAssessment
                            ? "bg-purple-50/40 border-purple-200 shadow-xs"
                            : isRevision
                            ? "bg-indigo-50/30 border-indigo-200 shadow-xs"
                            : isWeak
                            ? "bg-amber-50/40 border-amber-200 shadow-xs"
                            : isHigh
                            ? "bg-rose-50/30 border-rose-200/90 shadow-xs"
                            : "bg-slate-50/50 border-gray-200"
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                          {/* Checkbox + Details */}
                          <div className="flex items-start gap-3 flex-1 min-w-0">
                            <button
                              type="button"
                              onClick={() => toggleItemDone(item.topic_id)}
                              className="mt-0.5 text-gray-400 hover:text-emerald-600 transition-colors shrink-0"
                              title={isDone ? "Mark as in-progress" : "Mark as completed"}
                            >
                              {isDone ? (
                                <CheckSquare className="h-5 w-5 text-emerald-600 fill-emerald-100" />
                              ) : (
                                <Square className="h-5 w-5 hover:text-indigo-600" />
                              )}
                            </button>

                            <div className="flex-1 min-w-0">
                              {/* Badges: Unit + Priority + Status */}
                              <div className="flex items-center gap-1.5 flex-wrap mb-1">
                                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600">
                                  {item.unit_title}
                                </span>

                                {isAssessment ? (
                                  <span className="flex items-center gap-1 rounded-full bg-purple-100 border border-purple-200 px-2 py-0.5 text-[10px] font-bold text-purple-800">
                                    <GraduationCap className="h-3 w-3 text-purple-700" />
                                    <span>Master Assessment (≥65% Required)</span>
                                  </span>
                                ) : isRevision ? (
                                  <span className="flex items-center gap-1 rounded-full bg-indigo-100 border border-indigo-200 px-2 py-0.5 text-[10px] font-bold text-indigo-800">
                                    <RotateCcw className="h-3 w-3 text-indigo-700" />
                                    <span>Revision & Practice</span>
                                  </span>
                                ) : isHigh ? (
                                  <span className="flex items-center gap-1 rounded-full bg-rose-100 border border-rose-200 px-2 py-0.5 text-[10px] font-bold text-rose-800">
                                    <Flame className="h-3 w-3 fill-rose-500 text-rose-600" />
                                    <span>High Study Priority</span>
                                  </span>
                                ) : isMedium ? (
                                  <span className="flex items-center gap-1 rounded-full bg-amber-100 border border-amber-200 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                                    <Star className="h-3 w-3 fill-amber-500 text-amber-600" />
                                    <span>Medium Study Priority</span>
                                  </span>
                                ) : (
                                  <span className="rounded-full bg-slate-100 border border-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-700">
                                    <span>Lower Study Priority</span>
                                  </span>
                                )}

                                {isWeak && (
                                  <span className="rounded-full bg-amber-100 border border-amber-300 px-2 py-0.5 text-[10px] font-extrabold text-amber-900">
                                    ⚠️ Needs Revision
                                  </span>
                                )}

                                {item.status === "COMPLETED" && (
                                  <span className="rounded-full bg-emerald-100 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                                    ✓ Mastered
                                  </span>
                                )}
                              </div>

                              {/* Topic Name */}
                              <h4
                                className={`text-base font-bold text-gray-900 ${
                                  isDone ? "line-through text-gray-400" : ""
                                }`}
                              >
                                {item.topic_name}
                              </h4>

                              {/* Source Reference Scope */}
                              <div className="mt-1 flex items-center gap-2 text-xs text-gray-500 flex-wrap">
                                <span>📍 Source: <strong>{item.source_reference || "Course Slides"}</strong></span>
                                {item.best_score !== undefined && item.best_score !== null && (
                                  <span>• Last Score: <strong>{item.best_score}%</strong></span>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Time & Action Button */}
                          <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 shrink-0 pl-8 sm:pl-0">
                            {/* Human-friendly time block */}
                            <span className="flex items-center gap-1.5 rounded-xl bg-white border border-gray-200 px-3 py-1.5 text-xs font-extrabold text-gray-800 shadow-2xs">
                              <Clock3 className="h-3.5 w-3.5 text-indigo-600" />
                              <span>{formatMinutes(item.allocated_minutes || item.study_minutes)}</span>
                            </span>

                            {/* Direct Navigation to Topic Learning Page */}
                            {item.topic_id && !item.topic_id.startsWith("rev-") && !item.topic_id.startsWith("practice-") && !item.topic_id.startsWith("assess-") ? (
                              <Link
                                href={`/topics/${item.topic_id}`}
                                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-indigo-700 transition-colors"
                              >
                                <span>Open Learning Page</span>
                                <ArrowRight className="h-3.5 w-3.5" />
                              </Link>
                            ) : isAssessment ? (
                              <Link
                                href={`/subjects/${plan.subject_id}`}
                                className="inline-flex items-center gap-1.5 rounded-xl bg-purple-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-purple-700 transition-colors"
                              >
                                <span>Start Master Quiz</span>
                                <ArrowRight className="h-3.5 w-3.5" />
                              </Link>
                            ) : null}
                          </div>
                        </div>

                        {/* Collapsible Priority Reasons */}
                        {item.priority_reasons && item.priority_reasons.length > 0 && (
                          <div className="mt-3 pt-2.5 border-t border-gray-200/50 pl-8 text-xs text-gray-600">
                            <div className="flex items-center gap-1 font-semibold text-gray-700 mb-1">
                              <Info className="h-3.5 w-3.5 text-indigo-500" />
                              <span>Why this allocation & priority:</span>
                            </div>
                            <ul className="list-disc list-inside space-y-0.5 text-[11px] text-gray-500">
                              {item.priority_reasons.map((r, rIdx) => (
                                <li key={rIdx}>{r}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Roadmap Action Checklist */}
                        {item.tasks && item.tasks.length > 0 && (
                          <div className="mt-3 pt-2.5 border-t border-gray-200/50 pl-8">
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] font-bold text-gray-700">Roadmap Action Steps:</span>
                            </div>
                            <div className="grid gap-1.5 sm:grid-cols-3 mt-1.5">
                              {item.tasks.map((task, tIdx) => {
                                const key = `${item.topic_id}-${tIdx}`;
                                const isTaskChecked = !!completedTasks[key] || isDone;
                                return (
                                  <label
                                    key={tIdx}
                                    onClick={() => toggleTask(key)}
                                    className={`flex items-center gap-2 p-2 rounded-xl border text-xs cursor-pointer select-none transition-all ${
                                      isTaskChecked
                                        ? "bg-emerald-50 border-emerald-200 text-emerald-900 line-through"
                                        : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
                                    }`}
                                  >
                                    <input
                                      type="checkbox"
                                      checked={isTaskChecked}
                                      onChange={() => {}}
                                      className="rounded text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5 shrink-0"
                                    />
                                    <span className="truncate text-[11px]">{task}</span>
                                  </label>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
