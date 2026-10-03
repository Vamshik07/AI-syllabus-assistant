"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { CalendarDays, Clock3, FileText, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { Subject, StudyPlan } from "@/types";
import { useAuth } from "@/context/AuthContext";

const today = new Date().toISOString().slice(0, 10);

export default function TimetablePage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(today);
  const [dailyHours, setDailyHours] = useState("2");
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isAuthenticated) {
      api.getSubjects().then((items) => {
        setSubjects(items);
        if (items.length > 0) setSubjectId(items[0].id);
      }).catch((err) => setError(err.message));
    }
  }, [isAuthenticated]);

  const groupedSchedule = useMemo(() => {
    if (!plan) return [];
    const grouped = new Map<string, StudyPlan["schedule"]>();
    plan.schedule.forEach((item) => grouped.set(item.date, [...(grouped.get(item.date) || []), item]));
    return Array.from(grouped.entries());
  }, [plan]);

  const generatePlan = async (event: FormEvent) => {
    event.preventDefault();
    if (!subjectId) return;
    setLoading(true);
    setError("");
    try {
      setPlan(await api.createStudyPlan(subjectId, {
        start_date: startDate,
        end_date: endDate,
        daily_hours: Number(dailyHours),
      }));
    } catch (err: any) {
      setError(err.message || "Could not create the timetable.");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) return <div className="text-sm text-gray-500">Loading...</div>;
  if (!isAuthenticated) return <div className="rounded-2xl bg-white p-8 text-center">Sign in to create a timetable.</div>;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2 text-indigo-600"><CalendarDays className="h-5 w-5" /><span className="text-xs font-bold uppercase tracking-wider">Preparation planner</span></div>
        <h1 className="mt-2 text-3xl font-extrabold text-gray-900">Build your study timetable</h1>
        <p className="mt-1 text-sm text-gray-500">Choose a preparation period and the plan will distribute your syllabus with source-grounded material.</p>
      </div>

      <form onSubmit={generatePlan} className="grid gap-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm md:grid-cols-4">
        <label className="text-xs font-semibold text-gray-700">Subject
          <select value={subjectId} onChange={(e) => setSubjectId(e.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 p-2.5 text-sm">
            {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold text-gray-700">Start date
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 p-2.5 text-sm" required />
        </label>
        <label className="text-xs font-semibold text-gray-700">End date
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 p-2.5 text-sm" required />
        </label>
        <label className="text-xs font-semibold text-gray-700">Hours per day
          <input type="number" min="0.5" max="24" step="0.5" value={dailyHours} onChange={(e) => setDailyHours(e.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 p-2.5 text-sm" required />
        </label>
        <button disabled={loading || subjects.length === 0} className="md:col-span-4 inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-50">
          <Sparkles className="h-4 w-4" /> {loading ? "Creating plan..." : "Create timetable"}
        </button>
      </form>

      {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {plan && <div className="flex flex-wrap gap-3 text-xs font-semibold">
        <span className="rounded-full bg-indigo-50 px-3 py-1.5 text-indigo-700">{plan.total_hours} total hours</span>
        <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-emerald-700">{plan.material_mode === "detailed" ? "Detailed material" : "Concise key points"}</span>
      </div>}

      <div className="flex flex-col gap-5">
        {groupedSchedule.map(([date, items]) => (
          <section key={date} className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="flex items-center gap-2 border-b border-gray-100 pb-3 text-lg font-bold text-gray-900"><CalendarDays className="h-5 w-5 text-indigo-600" />{new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" })}</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {items.map((item) => (
                <article key={item.topic_id} className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-4">
                  <div className="flex items-start justify-between gap-3"><div><p className="text-[11px] font-semibold uppercase tracking-wide text-indigo-600">{item.unit_title}</p><h3 className="mt-1 font-bold text-gray-900">{item.topic_name}</h3></div><span className="flex shrink-0 items-center gap-1 rounded-full bg-white px-2 py-1 text-xs font-semibold text-gray-600"><Clock3 className="h-3.5 w-3.5" />{item.study_minutes} min</span></div>
                  <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-gray-600"><FileText className="h-3.5 w-3.5" />{item.material_mode === "detailed" ? "Detailed study material" : "Main points"}</div>
                  <p className="mt-2 whitespace-pre-line text-sm leading-6 text-gray-700">{item.material}</p>
                  <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-gray-600">{item.tasks.map((task) => <li key={task}>{task}</li>)}</ul>
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
