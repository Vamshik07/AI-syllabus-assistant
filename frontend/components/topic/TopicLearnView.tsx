"use client";

import React from "react";
import { Topic, TopicContentView, TopicLearningData } from "@/types";
import {
  BookOpen,
  Award,
  Sparkles,
  Layers,
  HelpCircle,
  FileText,
  ListOrdered,
  CheckCircle,
  AlertCircle,
  Image as ImageIcon,
  Tag,
  Scale,
  ThumbsUp,
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
  Table as TableIcon,
} from "lucide-react";
import { getMediaUrl } from "@/lib/utils";

interface TopicLearnViewProps {
  topic: Topic;
  content: TopicContentView;
  onSelectTab: (tab: any) => void;
}

export default function TopicLearnView({ topic, content, onSelectTab }: TopicLearnViewProps) {
  const learningData: TopicLearningData = content.learning_data || topic.learning_data || {};
  const pyqFrequency = content.pyq_frequency || topic.pyq_frequency || 0;
  const pyqNotes = content.pyq_notes || topic.pyq_notes;

  const summary = learningData.summary;
  const definitions = learningData.definitions || [];
  const coreConcepts = learningData.core_concepts || [];
  const characteristics = learningData.characteristics || [];
  const classifications = learningData.types_and_classifications || learningData.classifications || [];
  const processes = learningData.processes || [];
  const comparisons = learningData.comparisons || [];
  const advantages = learningData.advantages || [];
  const disadvantages = learningData.disadvantages || [];
  const examples = learningData.examples || [];
  const importantPoints = learningData.important_points || [];
  const rawSections = learningData.source_sections || [];
  const seenSectionTexts = new Set<string>();
  const sourceSections = rawSections.filter((section) => {
    const norm = section.text?.replace(/\s+/g, " ").trim().toLowerCase();
    if (!norm || seenSectionTexts.has(norm)) {
      return false;
    }
    seenSectionTexts.add(norm);
    return true;
  });

  const rawVisuals = learningData.visuals || [];
  const seenVisualKeys = new Set<string>();
  const visuals = rawVisuals.filter((vis) => {
    const key = vis.media_path || vis.content_html || vis.caption;
    if (!key || seenVisualKeys.has(key)) {
      return false;
    }
    seenVisualKeys.add(key);
    return true;
  });
  const keywords = learningData.keywords || [];

  return (
    <div className="flex flex-col gap-8">
      {/* PYQ Highlight Banner if frequently asked */}
      {pyqFrequency > 0 && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50/80 p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-amber-500 p-2 text-white shadow-sm">
              <Award className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-amber-900 text-sm">
                  High Exam Priority: Appeared in PYQs {pyqFrequency} {pyqFrequency === 1 ? "time" : "times"}
                </span>
                <span className="rounded-full bg-amber-200/80 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                  Exam Focus
                </span>
              </div>
              {pyqNotes ? (
                <p className="mt-1 text-xs text-amber-800 leading-relaxed">{pyqNotes}</p>
              ) : (
                <p className="mt-1 text-xs text-amber-800">
                  Questions related to this topic have appeared repeatedly in past semester papers. Focus on definitions and step-by-step processes.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button
          onClick={() => onSelectTab("keywords")}
          className="flex items-center gap-2.5 rounded-xl border border-gray-200 bg-white p-3.5 text-left shadow-sm hover:border-purple-400 hover:shadow-md transition-all group"
        >
          <div className="rounded-lg bg-purple-50 p-2 text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition-colors">
            <Tag className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-gray-900">Important Key Words</div>
            <div className="text-[11px] text-gray-500">
              {keywords.length} key terms
            </div>
          </div>
        </button>

        {visuals.length > 0 && (
          <button
            onClick={() => onSelectTab("diagrams")}
            className="flex items-center gap-2.5 rounded-xl border border-gray-200 bg-white p-3.5 text-left shadow-sm hover:border-emerald-400 hover:shadow-md transition-all group"
          >
            <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
              <ImageIcon className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-gray-900">Diagrams</div>
              <div className="text-[11px] text-gray-500">
                {visuals.length} available
              </div>
            </div>
          </button>
        )}

        <button
          onClick={() => onSelectTab("quiz")}
          className="flex items-center gap-2.5 rounded-xl border border-gray-200 bg-white p-3.5 text-left shadow-sm hover:border-indigo-400 hover:shadow-md transition-all group"
        >
          <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
            <HelpCircle className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-gray-900">Topic Quiz</div>
            <div className="text-[11px] text-gray-500">Test understanding</div>
          </div>
        </button>

        <button
          onClick={() => onSelectTab("practice")}
          className="flex items-center gap-2.5 rounded-xl border border-gray-200 bg-white p-3.5 text-left shadow-sm hover:border-amber-400 hover:shadow-md transition-all group"
        >
          <div className="rounded-lg bg-amber-50 p-2 text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition-colors">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-gray-900">Practice Cards</div>
            <div className="text-[11px] text-gray-500">Active recall</div>
          </div>
        </button>
      </div>

      {/* 0. Grounded Topic Summary */}
      {summary && summary.trim().length > 0 && (
        <section className="rounded-2xl border border-indigo-100 bg-indigo-50/40 p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <div className="rounded-md bg-indigo-600 p-1 text-white">
              <Lightbulb className="h-3.5 w-3.5" />
            </div>
            <h2 className="font-bold text-indigo-950 text-xs uppercase tracking-wider">
              Topic Summary & Core Overview
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-gray-800 leading-relaxed font-medium">
            {summary}
          </p>
        </section>
      )}

      {(sourceSections.length > 0 || visuals.length > 0) && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <div className="rounded-lg bg-indigo-50 p-1.5 text-indigo-600">
              <BookOpen className="h-4 w-4" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900 text-base">
                {sourceSections.length > 0 ? "Study Notes & Material" : "Visual Process & Concept Diagram"}
              </h2>
              <p className="text-xs text-gray-500">
                {sourceSections.length > 0
                  ? "Structured syllabus text and explanations for this topic"
                  : "Core concept and process illustrated directly from the source"}
              </p>
            </div>
          </div>

          {/* Standalone visual diagram view when topic is purely diagram-driven */}
          {sourceSections.length === 0 && visuals.length > 0 && (
            <div className="flex flex-col gap-6">
              {visuals.map((vis, idx) => (
                <div key={idx} className="flex flex-col rounded-xl border border-indigo-100 bg-white overflow-hidden shadow-xs">
                  {vis.media_path && (
                    <div className="flex items-center justify-center p-4 bg-gray-50/50 min-h-[220px]">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={getMediaUrl(vis.media_path)}
                        alt={vis.caption || "Topic diagram"}
                        className="max-h-[360px] w-auto max-w-full rounded-lg object-contain border border-gray-100 bg-white shadow-2xs"
                      />
                    </div>
                  )}
                  {vis.content_html && (
                    <div className="p-4 overflow-x-auto" dangerouslySetInnerHTML={{ __html: vis.content_html }} />
                  )}
                  <div className="p-3 bg-white border-t border-gray-100 text-center">
                    <span className="font-semibold text-gray-900 text-sm">{vis.caption || `${topic.name} Diagram`}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {sourceSections.length > 0 && (
          <div className="flex flex-col gap-6">
            {(() => {
              const matchedVisualIds = new Set<string>();
              return sourceSections.map((section, index) => {
                // 1. Check if section text explicitly mentions a figure number that matches a diagram caption
                let matchingVisual = visuals.find((v) => {
                  if (!v.media_path) return false;
                  const vKey = v.id || v.media_path;
                  if (matchedVisualIds.has(vKey)) return false;
                  if (v.caption && section.text) {
                    const capNum = v.caption.match(/Figure\s*(\d+(?:\.\d+)*)/i);
                    if (capNum && section.text.toLowerCase().includes(capNum[0].toLowerCase())) {
                      return true;
                    }
                  }
                  return false;
                });

                // 2. If section is a table placeholder, match to corresponding table visual
                if (!matchingVisual && section.text?.toLowerCase().includes("table content")) {
                  matchingVisual = visuals.find((v) => {
                    if (v.type !== "TABLE" && !v.content_html) return false;
                    const vKey = v.id || v.caption || `table_${v.page_number || ""}`;
                    if (matchedVisualIds.has(vKey)) return false;
                    if (v.page_number && section.page_number && v.page_number === section.page_number) return true;
                    if (v.slide_number && section.slide_number && v.slide_number === section.slide_number) return true;
                    return true;
                  });
                }

                // 3. Fallback: match by page or slide number for diagrams
                if (!matchingVisual) {
                  matchingVisual = visuals.find((v) => {
                    if (!v.media_path) return false;
                    const vKey = v.id || v.media_path;
                    if (matchedVisualIds.has(vKey)) return false;
                    if (v.slide_number && v.slide_number === section.slide_number) return true;
                    if (v.page_number && v.page_number === section.page_number) return true;
                    return false;
                  });
                }

                if (matchingVisual) {
                  const vKey = matchingVisual.id || matchingVisual.media_path || matchingVisual.caption || `vis_${index}`;
                  matchedVisualIds.add(vKey);
                }

                const isTablePlaceholder = section.text?.trim().toLowerCase().startsWith("table content on page");

                return (
                  <article key={index} className="border-l-2 border-indigo-200 pl-4 py-1 flex flex-col gap-3">
                    {/* Show section text unless it's just a raw table placeholder that has an HTML table */}
                    {(!isTablePlaceholder || !matchingVisual?.content_html) && (
                      <p className="whitespace-pre-wrap text-sm leading-7 text-gray-800">{section.text}</p>
                    )}

                    {/* Inlined HTML Table */}
                    {matchingVisual && matchingVisual.content_html && (
                      <div className="mt-2 overflow-x-auto rounded-xl border border-gray-200 bg-white p-3 shadow-xs">
                        <div dangerouslySetInnerHTML={{ __html: matchingVisual.content_html }} />
                        {matchingVisual.caption && !matchingVisual.caption.includes("Table") && (
                          <div className="mt-2 text-xs font-semibold text-gray-700">
                            {matchingVisual.caption}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Inlined Diagram / Image */}
                    {matchingVisual && matchingVisual.media_path && (
                      <div className="mt-2 flex flex-col items-center sm:items-start max-w-lg rounded-xl border border-gray-200 bg-gray-50/50 p-3 shadow-2xs">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={getMediaUrl(matchingVisual.media_path)}
                          alt={matchingVisual.caption || "Topic diagram"}
                          className="max-h-[280px] w-auto max-w-full rounded-lg object-contain bg-white border border-gray-100"
                        />
                        <div className="mt-2 text-xs font-semibold text-gray-700">
                          {matchingVisual.caption}
                        </div>
                      </div>
                    )}
                  </article>
                );
              });
            })()}
          </div>
          )}

          {/* Any other authentic topic diagrams not matched to a specific section */}
          {(() => {
            const unmatchedVisuals = visuals.filter((v) => {
              if (!v.media_path) return false;
              // Check if already matched
              return !sourceSections.some((s) => {
                const capNum = v.caption ? v.caption.match(/Figure\s*(\d+(?:\.\d+)*)/i) : null;
                if (capNum && s.text?.toLowerCase().includes(capNum[0].toLowerCase())) return true;
                if (v.slide_number && v.slide_number === s.slide_number) return true;
                if (v.page_number && v.page_number === s.page_number) return true;
                return false;
              });
            });

            if (unmatchedVisuals.length === 0) return null;

            return (
              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-center gap-2 mb-3">
                  <div className="rounded-lg bg-emerald-50 p-1.5 text-emerald-600">
                    <ImageIcon className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 text-sm">Additional Topic Diagrams</h3>
                    <p className="text-xs text-gray-500">Visual illustrations and schematics belonging to this topic</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {unmatchedVisuals.map((vis, idx) => (
                    <div key={idx} className="flex flex-col rounded-xl border border-gray-200 bg-white overflow-hidden shadow-xs">
                      {vis.media_path && (
                        <div className="flex items-center justify-center p-3 bg-gray-50/50 min-h-[180px]">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={getMediaUrl(vis.media_path)}
                            alt={vis.caption || "Topic diagram"}
                            className="max-h-[300px] w-auto max-w-full rounded-lg object-contain border border-gray-100 bg-white"
                          />
                        </div>
                      )}
                      <div className="p-2.5 bg-white border-t border-gray-100 text-center">
                        <span className="font-semibold text-gray-800 text-xs">{vis.caption}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </section>
      )}

      {/* 1. Grounded Important Keywords for Fast Memory Recall */}
      {keywords.length > 0 && (
        <section className="rounded-2xl border border-purple-200 bg-purple-50/20 p-6 shadow-sm">
          <div className="flex items-center justify-between gap-2 mb-4 border-b border-purple-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="rounded-lg bg-purple-600 p-1.5 text-white">
                <Tag className="h-4 w-4" />
              </div>
              <div>
                <h2 className="font-bold text-gray-900 text-base">Important Keywords & Academic Terms</h2>
                <p className="text-xs text-gray-500">Core keywords extracted from source to remember this topic easily</p>
              </div>
            </div>
            <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-bold text-purple-700">
              {keywords.length} Key Terms
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {keywords.map((kw, idx) => {
              const term = kw.keyword || (kw as any).term || "Keyword";
              const expl = kw.explanation || (kw as any).definition || "";
              return (
                <div
                  key={idx}
                  className="flex flex-col justify-between rounded-xl border border-purple-100 bg-white p-4 shadow-2xs hover:border-purple-300 transition-colors"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1.5 mb-1.5">
                      <h3 className="font-bold text-purple-950 text-xs sm:text-sm">{term}</h3>
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded">
                        Key Term
                      </span>
                    </div>
                    {expl && <p className="text-xs text-gray-600 leading-relaxed">{expl}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 1. Definitions Section */}
      {definitions.length > 0 && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <div className="rounded-lg bg-indigo-50 p-1.5 text-indigo-600">
              <BookOpen className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-gray-900 text-base">Key Definitions</h2>
            <span className="text-xs font-medium text-gray-400">Grounded in source</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {definitions.map((def, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-indigo-100 bg-indigo-50/30 p-4 transition-all hover:bg-indigo-50/60"
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <h3 className="font-bold text-indigo-950 text-sm">{def.term}</h3>
                </div>
                <p className="text-xs text-gray-700 leading-relaxed">{def.definition}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 2. Core Concepts Section */}
      {coreConcepts.length > 0 && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <div className="rounded-lg bg-purple-50 p-1.5 text-purple-600">
              <Sparkles className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-gray-900 text-base">Core Concepts & Explanations</h2>
          </div>
          <div className="flex flex-col gap-4">
            {coreConcepts.map((item, idx) => {
              const title = item.concept || item.title || "Concept";
              const desc = item.explanation || item.description || "";
              return (
                <div
                  key={idx}
                  className="rounded-xl border border-gray-200 bg-gray-50/50 p-4 hover:border-purple-200 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <h3 className="font-bold text-gray-900 text-sm">{title}</h3>
                  </div>
                  <p className="text-xs text-gray-700 leading-relaxed">{desc}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 3. Characteristics & Features */}
      {characteristics.length > 0 && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <div className="rounded-lg bg-emerald-50 p-1.5 text-emerald-600">
              <Layers className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-gray-900 text-base">Key Characteristics & Features</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {characteristics.map((item, idx) => {
              const name = typeof item === "string" ? item : item.name;
              const desc = typeof item === "object" ? item.description : null;
              const ref = typeof item === "object" ? item.source_reference : null;
              return (
                <div
                  key={idx}
                  className="flex flex-col justify-between rounded-xl border border-emerald-100 bg-emerald-50/20 p-4"
                >
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                      <h3 className="font-bold text-gray-900 text-xs">{name}</h3>
                    </div>
                    {desc && <p className="text-xs text-gray-600 leading-relaxed">{desc}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 4. Types & Classifications */}
      {classifications.length > 0 && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <div className="rounded-lg bg-teal-50 p-1.5 text-teal-600">
              <Layers className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-gray-900 text-base">Types & Classifications</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {classifications.map((cls, idx) => (
              <div key={idx} className="rounded-xl border border-teal-100 bg-teal-50/20 p-4">
                <h3 className="font-bold text-teal-950 text-sm mb-1.5">{cls.category}</h3>
                {cls.description && (
                  <p className="text-xs text-gray-700 leading-relaxed mb-2.5">{cls.description}</p>
                )}
                {cls.items && cls.items.length > 0 && (
                  <ul className="flex flex-wrap gap-1.5">
                    {cls.items.map((it, iIdx) => (
                      <li key={iIdx} className="rounded-md bg-white border border-teal-200 px-2 py-0.5 text-xs text-teal-800 font-medium">
                        {it}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 5. Processes & Step-by-Step Sequences */}
      {processes.length > 0 && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="rounded-lg bg-blue-50 p-1.5 text-blue-600">
                <ListOrdered className="h-4 w-4" />
              </div>
              <h2 className="font-bold text-gray-900 text-base">Process & Execution Steps</h2>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            {processes.map((proc, pIdx) => {
              const pName = proc.process_name || proc.name || "Process Steps";
              return (
                <div key={pIdx} className="rounded-xl border border-blue-100 bg-blue-50/20 p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-blue-950 text-sm">{pName}</h3>
                  </div>

                  <div className="flex flex-col gap-3">
                    {proc.steps.map((st, sIdx) => {
                      const title = typeof st === "string" ? st : st.title;
                      const desc = typeof st === "object" ? st.description : null;
                      const stepNum = typeof st === "object" && st.step_number ? st.step_number : sIdx + 1;
                      return (
                        <div
                          key={sIdx}
                          className="flex items-start gap-3 rounded-lg border border-white bg-white/90 p-3 shadow-2xs"
                        >
                          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white font-bold text-xs">
                            {stepNum}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between gap-2">
                              <h4 className="font-bold text-gray-900 text-xs">{title}</h4>
                            </div>
                            {desc && desc !== title && (
                              <p className="mt-0.5 text-xs text-gray-600 leading-relaxed">
                                {desc}
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 6. Comparisons & Differences */}
      {comparisons.length > 0 && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <div className="rounded-lg bg-indigo-50 p-1.5 text-indigo-600">
              <Scale className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-gray-900 text-base">Key Comparisons & Differences</h2>
          </div>
          <div className="flex flex-col gap-3">
            {comparisons.map((cmp, idx) => (
              <div key={idx} className="rounded-xl border border-gray-200 bg-gray-50/40 p-4">
                <div className="font-bold text-xs text-gray-900 mb-2">{cmp.aspect}</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="rounded-lg bg-white border border-gray-200 p-2.5">
                    <span className="font-semibold text-gray-700 block mb-1">Perspective A:</span>
                    <p className="text-gray-600 leading-relaxed">{cmp.item_a}</p>
                  </div>
                  <div className="rounded-lg bg-white border border-gray-200 p-2.5">
                    <span className="font-semibold text-gray-700 block mb-1">Perspective B:</span>
                    <p className="text-gray-600 leading-relaxed">{cmp.item_b}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 7. Advantages & Benefits */}
      {advantages.length > 0 && (
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50/20 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-emerald-100 pb-3">
            <div className="rounded-lg bg-emerald-100 p-1.5 text-emerald-700">
              <ThumbsUp className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-emerald-950 text-base">Key Advantages & Benefits</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {advantages.map((adv, idx) => {
              const text = typeof adv === "string" ? adv : adv.point;
              return (
                <div key={idx} className="flex items-start gap-2.5 rounded-xl border border-emerald-100 bg-white p-3.5 shadow-2xs">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                  <p className="text-xs text-gray-800 leading-relaxed">{text}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 8. Disadvantages & Limitations */}
      {disadvantages.length > 0 && (
        <section className="rounded-2xl border border-red-200 bg-red-50/20 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-red-100 pb-3">
            <div className="rounded-lg bg-red-100 p-1.5 text-red-700">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-red-950 text-base">Disadvantages & Limitations</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {disadvantages.map((dis, idx) => {
              const text = typeof dis === "string" ? dis : dis.point;
              return (
                <div key={idx} className="flex items-start gap-2.5 rounded-xl border border-red-100 bg-white p-3.5 shadow-2xs">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500 shrink-0 mt-1.5" />
                  <p className="text-xs text-gray-800 leading-relaxed">{text}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 9. Concrete Examples & Applications */}
      {examples.length > 0 && (
        <section className="rounded-2xl border border-blue-200 bg-blue-50/20 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-blue-100 pb-3">
            <div className="rounded-lg bg-blue-100 p-1.5 text-blue-700">
              <Lightbulb className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-blue-950 text-base">Concrete Examples & Applications</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {examples.map((ex, idx) => {
              const text = typeof ex === "string" ? ex : ex.example;
              return (
                <div key={idx} className="rounded-xl border border-blue-100 bg-white p-3.5 shadow-2xs">
                  <p className="text-xs text-gray-800 leading-relaxed">{text}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 10. Important Points to Remember */}
      {importantPoints.length > 0 && (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <div className="rounded-lg bg-amber-50 p-1.5 text-amber-600">
              <AlertCircle className="h-4 w-4" />
            </div>
            <h2 className="font-bold text-gray-900 text-base">Key Points for Revision</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {importantPoints.map((pt, idx) => {
              const text = typeof pt === "string" ? pt : pt.point;
              const ref = typeof pt === "object" ? pt.source_reference : null;
              return (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 rounded-xl border border-amber-100 bg-amber-50/30 p-3.5"
                >
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-800 leading-relaxed font-medium">{text}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Assessment Call-To-Action */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 rounded-2xl border border-indigo-200 bg-linear-to-r from-indigo-50 to-purple-50 p-6 shadow-sm">
        <div>
          <h3 className="font-bold text-indigo-950 text-base">Ready to test your topic comprehension?</h3>
          <p className="mt-0.5 text-xs text-indigo-700">
            Verify your mastery across definitions, concepts, and steps with source-grounded questions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectTab("practice")}
            className="rounded-xl border border-indigo-300 bg-white px-4 py-2 text-xs font-bold text-indigo-700 hover:bg-indigo-50 shadow-2xs"
          >
            Practice Cards
          </button>
          <button
            onClick={() => onSelectTab("quiz")}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-indigo-700 transition-transform hover:scale-105"
          >
            <HelpCircle className="h-4 w-4" />
            <span>Take Topic Quiz</span>
          </button>
        </div>
      </div>
    </div>
  );
}
