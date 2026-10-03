"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  BookOpen,
  GraduationCap,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  FileText,
  FileCheck,
  Award,
  Sparkles,
  Layers,
  Lock,
  Compass,
  BarChart3,
  HelpCircle,
  Eye,
  AlertTriangle,
} from "lucide-react";

export default function LandingPage() {
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="flex flex-col gap-16 pb-16">
      {/* Logged in Quick Access Banner */}
      {isAuthenticated && user && (
        <div className="rounded-2xl border border-indigo-200 bg-indigo-50/80 p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center gap-3.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white font-bold text-sm">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900">
                Welcome back, {user.name}!
              </p>
              <p className="text-xs text-indigo-700">
                You are currently logged in. Jump straight to your study materials.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <Link
              href="/subjects"
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm transition-all hover:scale-105"
            >
              <span>Open My Subjects</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <Link
              href="/progress"
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 rounded-xl border border-indigo-300 bg-white px-4 py-2.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-50 transition-colors"
            >
              <span>View Progress</span>
            </Link>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-950 via-indigo-900 to-slate-900 px-6 py-16 sm:px-12 sm:py-20 text-white shadow-2xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-800/80 px-3.5 py-1.5 text-xs font-semibold text-indigo-200 border border-indigo-500/30 backdrop-blur mb-6">
            <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>100% Source-Grounded Learning • Zero AI Hallucinations</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight sm:leading-tight">
            Learn from Authentic Course Sources, <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-sky-200 to-indigo-100">Never Rewritten by AI.</span>
          </h1>

          <p className="mt-5 text-sm sm:text-base text-indigo-100 leading-relaxed max-w-2xl">
            Upload your authentic curriculum files (PDF, PPTX, DOCX). AI Syllabus Assistant organizes your materials into structured topic pathways and displays the original slides, diagrams, and pages. Test your mastery with teacher-grade quizzes with verifiable citations.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            {isAuthenticated ? (
              <Link
                href="/subjects"
                className="flex items-center gap-2.5 rounded-xl bg-white px-6 py-3.5 text-xs sm:text-sm font-bold text-indigo-950 shadow-lg hover:bg-indigo-50 transition-all hover:scale-105"
              >
                <BookOpen className="h-4 w-4 text-indigo-700" />
                <span>Go to Enrolled Subjects</span>
                <ArrowRight className="h-4 w-4 text-indigo-700" />
              </Link>
            ) : (
              <>
                <Link
                  href="/register"
                  className="flex items-center gap-2.5 rounded-xl bg-indigo-500 px-6 py-3.5 text-xs sm:text-sm font-bold text-white shadow-lg shadow-indigo-500/30 hover:bg-indigo-400 transition-all hover:scale-105"
                >
                  <GraduationCap className="h-4 w-4" />
                  <span>Get Started Free</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/login"
                  className="flex items-center gap-2 rounded-xl bg-white/10 border border-white/20 backdrop-blur px-5 py-3.5 text-xs sm:text-sm font-semibold text-white hover:bg-white/20 transition-colors"
                >
                  <span>Sign In</span>
                </Link>
              </>
            )}
            <a
              href="#how-it-works"
              className="flex items-center gap-1.5 px-4 py-3 text-xs sm:text-sm font-medium text-indigo-200 hover:text-white transition-colors"
            >
              <span>See how it works</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </a>
          </div>

          {/* Quick Trust Badges */}
          <div className="mt-10 pt-8 border-t border-indigo-800/60 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs text-indigo-200">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>Exact Slide & Page Layouts</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>Verifiable Citations</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>Multi-User Isolated Progress</span>
            </div>
          </div>
        </div>

        {/* Ambient background glow */}
        <div className="pointer-events-none absolute -right-24 -bottom-24 h-96 w-96 rounded-full bg-indigo-500/15 blur-3xl" />
        <div className="pointer-events-none absolute right-16 top-8 h-60 w-60 rounded-full bg-sky-400/10 blur-2xl" />
      </section>

      {/* The Core Difference: Generic AI vs AI Syllabus Assistant */}
      <section className="flex flex-col gap-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-600 mb-1">
            Why AI Syllabus Assistant?
          </h2>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
            Education Demands Absolute Truth, Not AI Speculation.
          </h3>
          <p className="mt-2 text-xs sm:text-sm text-gray-500">
            Most AI learning tools summarize, rewrite, or hallucinate answers. AI Syllabus Assistant keeps your original document as the single authoritative source of truth.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          {/* Traditional AI Box */}
          <div className="rounded-2xl border border-red-200 bg-red-50/40 p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2.5 text-red-700 font-bold text-sm mb-3">
                <AlertTriangle className="h-5 w-5" />
                <span>The Problem: Generic AI Tools</span>
              </div>
              <ul className="space-y-3 text-xs text-red-900/80 leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="text-red-500 font-bold">✕</span>
                  <span><strong>Rewrites & Summarizes:</strong> Misses subtle exam-critical definitions and edge cases present in your syllabus.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-500 font-bold">✕</span>
                  <span><strong>Loses Visual Context:</strong> Drops crucial diagrams, flowchart steps, formulas, and slide tables.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-500 font-bold">✕</span>
                  <span><strong>Hallucinates:</strong> Generates plausible but fabricated facts that can cost points on exams.</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-red-200/60 text-[11px] font-medium text-red-700">
              Generic chatbots generate reconstructed text, not verified curriculum.
            </div>
          </div>

          {/* AI Syllabus Assistant Solution Box */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2.5 text-emerald-800 font-bold text-sm mb-3">
                <ShieldCheck className="h-5 w-5 text-emerald-600" />
                <span>The AI Syllabus Assistant Fidelity Guarantee</span>
              </div>
              <ul className="space-y-3 text-xs text-emerald-950/80 leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span><strong>Direct Original Content:</strong> See your authentic slides and textbook pages exactly as uploaded.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span><strong>Full Visual Preservation:</strong> Preserves charts, images, equations, and visual slide ordering.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span><strong>Teacher-Grade Quizzing:</strong> AI is only used to evaluate and frame conceptual questions grounded directly in the text.</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-emerald-200/60 text-[11px] font-medium text-emerald-800">
              100% fidelity: Original educational material is never replaced or altered.
            </div>
          </div>
        </div>
      </section>

      {/* Core Platform Features Grid */}
      <section className="flex flex-col gap-8">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-600 mb-1">
            Platform Capabilities
          </h2>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
            Engineered For Rigorous Academic Mastery
          </h3>
          <p className="mt-2 text-xs sm:text-sm text-gray-500">
            Everything you need to organize lecture notes, slide decks, and textbooks into step-by-step masterable units.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 mb-4">
              <FileCheck className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-gray-900">Multi-Format Ingestion</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Upload PDF documents, PowerPoint (.pptx) slide decks, or Word (.docx) documents. Intelligent extraction parses structures with built-in OCR fallback.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-50 text-sky-600 mb-4">
              <Layers className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-gray-900">Ordered Topic Pathways</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Documents are broken down into logical topics and subtopics following the original sequence of the resource, complete with exact slide/page references.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 mb-4">
              <Eye className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-gray-900">Authentic Slide/Page Viewer</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Study the exact visual slides and pages. No generic text blocks—see the authentic diagrams, tables, and typography your instructor authored.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-50 text-amber-600 mb-4">
              <Sparkles className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-gray-900">Teacher-Grade Quizzing</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Each topic automatically generates rigorous 5-question multiple choice quizzes testing real comprehension rather than simple fill-in-the-blank trivia.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-50 text-purple-600 mb-4">
              <Lock className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-gray-900">Sequential Mastery Gating</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Progress only when you know the material. Score ≥ 75% on a topic quiz to unlock the next topic and qualify for the Master Unit Quiz.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-50 text-rose-600 mb-4">
              <BarChart3 className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-gray-900">Per-User Isolated Analytics</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Secure individual accounts keep your learning pathway completely private. Monitor your progress bars across every subject and unit in real time.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="rounded-3xl border border-gray-200 bg-white p-8 sm:p-12 shadow-sm">
        <div className="text-center max-w-xl mx-auto mb-10">
          <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-600 mb-1">
            Workflow
          </h2>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-gray-900">
            How AI Syllabus Assistant Works
          </h3>
          <p className="mt-2 text-xs sm:text-sm text-gray-500">
            Start learning with guaranteed source fidelity in three simple steps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Step 1 */}
          <div className="flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white font-extrabold text-lg shadow-lg shadow-indigo-100 mb-4">
              1
            </div>
            <h4 className="text-base font-bold text-gray-900">Create Subject & Units</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Organize your curriculum into subjects (e.g. Distributed Systems) and define syllabus units for each module.
            </p>
          </div>

          {/* Step 2 */}
          <div className="flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white font-extrabold text-lg shadow-lg shadow-indigo-100 mb-4">
              2
            </div>
            <h4 className="text-base font-bold text-gray-900">Upload Authentic Resource</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Upload your official lecture PDF, PPTX slides, or Word doc. The system segments the file into strictly ordered topics.
            </p>
          </div>

          {/* Step 3 */}
          <div className="flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white font-extrabold text-lg shadow-lg shadow-indigo-100 mb-4">
              3
            </div>
            <h4 className="text-base font-bold text-gray-900">Study & Pass Quizzes</h4>
            <p className="mt-2 text-xs text-gray-500 leading-relaxed">
              Review original slides and text. Pass 5-question teacher quizzes to unlock the next topic and complete your unit.
            </p>
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="rounded-3xl bg-indigo-600 p-8 sm:p-12 text-center text-white shadow-xl flex flex-col items-center">
        <h3 className="text-2xl sm:text-3xl font-extrabold">
          Ready to Learn Without AI Hallucinations?
        </h3>
        <p className="mt-3 text-xs sm:text-sm text-indigo-100 max-w-lg">
          Join students who study with authentic source materials, verifiable citations, and rigorous comprehension testing.
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
          {isAuthenticated ? (
            <Link
              href="/subjects"
              className="rounded-xl bg-white px-6 py-3.5 text-xs sm:text-sm font-bold text-indigo-900 shadow-md hover:bg-indigo-50 transition-all hover:scale-105"
            >
              Enter Enrolled Subjects →
            </Link>
          ) : (
            <>
              <Link
                href="/register"
                className="rounded-xl bg-white px-6 py-3.5 text-xs sm:text-sm font-bold text-indigo-900 shadow-md hover:bg-indigo-50 transition-all hover:scale-105"
              >
                Create Free Account
              </Link>
              <Link
                href="/login"
                className="rounded-xl border border-white/30 bg-indigo-700/60 px-6 py-3.5 text-xs sm:text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
              >
                Sign In to Existing Account
              </Link>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
