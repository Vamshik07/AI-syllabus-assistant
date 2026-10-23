"use client";

import { useState } from "react";
import { TopicContentView, SourceRegion } from "@/types";
import { FileText, ShieldCheck, Image as ImageIcon, Table as TableIcon, Layers, Maximize2 } from "lucide-react";

interface SourceContentViewerProps {
  content: TopicContentView;
}

export default function SourceContentViewer({ content }: SourceContentViewerProps) {
  const [selectedSubtopic, setSelectedSubtopic] = useState<string | null>(null);

  // Filter regions if a subtopic is selected
  const visibleRegions = selectedSubtopic
    ? content.regions.filter(
        (r) => !r.subtopic_id || r.subtopic_id === selectedSubtopic
      )
    : content.regions;

  const fullPages = content.regions.filter((r) => r.region_type === "FULL_PAGE");
  const slides = content.regions.filter((r) => r.region_type === "SLIDE");

  return (
    <div className="flex flex-col gap-6">
      {/* Fidelity Header Guarantee Banner */}
      <div className="flex items-center justify-between rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50/80 via-white to-indigo-50/50 p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-gray-900 text-sm">Authoritative Source Content</h3>
              <span className="rounded bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
                100% Unaltered
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Original material from <span className="font-medium text-gray-700">{content.file_name}</span>. No AI rewriting or summarization.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="rounded-full bg-gray-100 px-2.5 py-1 font-mono font-medium">
            Format: {content.file_type}
          </span>
          {content.source_start && (
            <span className="rounded-full bg-gray-100 px-2.5 py-1 font-mono font-medium">
              Source: {content.file_type === 'PPTX' ? `Slide ${content.source_start}` : `Page ${content.source_start}`}
            </span>
          )}
        </div>
      </div>

      {/* Subtopics Navigation if available */}
      {content.subtopics.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 pb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 mr-2">
            Subtopics:
          </span>
          <button
            onClick={() => setSelectedSubtopic(null)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              selectedSubtopic === null
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            All Content
          </button>
          {content.subtopics.map((sub) => (
            <button
              key={sub.id}
              onClick={() => setSelectedSubtopic(sub.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                selectedSubtopic === sub.id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {sub.name}
            </button>
          ))}
        </div>
      )}

      {/* Source Regions Rendering */}
      <div className="flex flex-col gap-6">
        {content.file_type === "PDF" && fullPages.length > 0 ? (
          /* PDF Original Page View */
          <div className="flex flex-col gap-8">
            {fullPages.map((pageRegion) => (
              <div
                key={pageRegion.id}
                className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm"
              >
                <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/75 px-4 py-2.5 text-xs text-gray-600">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-indigo-600" />
                    <span className="font-semibold text-gray-800">Original PDF Page {pageRegion.page_number}</span>
                  </div>
                  <span className="text-[11px] font-mono text-gray-400">Authentic Page Render</span>
                </div>
                {pageRegion.media_path && (
                  <div className="flex justify-center bg-gray-100/50 p-4">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={`http://localhost:8000${pageRegion.media_path}`}
                      alt={`Page ${pageRegion.page_number}`}
                      className="max-w-full rounded-lg shadow-sm border border-gray-200 object-contain"
                    />
                  </div>
                )}
                {/* Fallback extracted text view if image fails or for copy/accessibility */}
                {pageRegion.content_text && (
                  <details className="border-t border-gray-100 px-4 py-3 text-xs text-gray-600">
                    <summary className="cursor-pointer font-medium text-indigo-600 hover:text-indigo-800">
                      View raw extracted page text
                    </summary>
                    <pre className="mt-2 whitespace-pre-wrap font-sans text-gray-700 leading-relaxed bg-gray-50 p-3 rounded-lg border border-gray-200">
                      {pageRegion.content_text}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        ) : content.file_type === "PPTX" && slides.length > 0 ? (
          /* PPTX Original Slide View */
          <div className="flex flex-col gap-6">
            {slides.map((slideRegion) => {
              // Extract clean slide title
              const rawTitle = slideRegion.source_reference?.includes(":")
                ? slideRegion.source_reference.split(":").slice(1).join(":").trim()
                : (slideRegion.source_reference || `Slide ${slideRegion.slide_number}`);

              const isGenericTitle = !rawTitle || rawTitle === "[No Title]" || rawTitle.toLowerCase().startsWith("slide ");
              const displayTitle = isGenericTitle ? null : rawTitle;

              // Clean text: strip any legacy OCR / Diagram Content dumps
              let displayText = (slideRegion.content_text || "").trim();

              // Remove any legacy "Diagram Content (...):" blocks
              displayText = displayText.replace(/Diagram Content\s*(\([^)]*\))?:?[\s\S]*?(?=\n\n[A-Z]|\n---|$)/gi, "").trim();

              // Strip redundant "Title: ..." prefix if present
              if (displayTitle) {
                const titlePrefixRegex = new RegExp(`^Title:\\s*${displayTitle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\n*`, 'i');
                displayText = displayText.replace(titlePrefixRegex, '').trim();
              }
              displayText = displayText.replace(/^Title:\s*[^\n]*\n?/i, "").trim();

              const slideImagesAndTables = visibleRegions.filter(
                (r) => r.slide_number === slideRegion.slide_number && r.id !== slideRegion.id
              );

              return (
                <div
                  key={slideRegion.id}
                  className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm"
                >
                  <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/75 px-4 py-2.5 text-xs text-gray-600">
                    <div className="flex items-center gap-2">
                      <Layers className="h-4 w-4 text-indigo-600" />
                      <span className="font-semibold text-gray-800">Original Slide {slideRegion.slide_number}</span>
                    </div>
                    <span className="text-[11px] font-mono text-gray-400">Authentic Slide Render</span>
                  </div>

                  <div className="p-6">
                    {displayTitle && (
                      <h4 className="text-xl font-bold text-gray-900 border-b border-gray-100 pb-3 mb-4">
                        {displayTitle}
                      </h4>
                    )}

                    {displayText ? (
                      <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap mb-4">
                        {displayText}
                      </div>
                    ) : null}

                    {/* Render any associated authentic images or tables on this slide */}
                    {slideImagesAndTables.length > 0 && (
                      <div className="flex flex-col gap-4">
                        {slideImagesAndTables.map((subRegion) => (
                          <div key={subRegion.id} className="mt-2 flex flex-col items-center">
                            {subRegion.region_type === "IMAGE" && subRegion.media_path && (
                              /* eslint-disable-next-line @next/next/no-img-element */
                              <img
                                src={`http://localhost:8000${subRegion.media_path}`}
                                alt={`Slide ${slideRegion.slide_number} Diagram`}
                                className="max-h-[520px] w-auto max-w-full rounded-xl border border-gray-200 shadow-sm object-contain bg-white"
                              />
                            )}
                            {subRegion.region_type === "TABLE" && subRegion.content_html && (
                              <div
                                className="w-full overflow-x-auto rounded-lg border border-gray-200"
                                dangerouslySetInnerHTML={{ __html: subRegion.content_html }}
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* DOCX & Structured Region View */
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="space-y-4">
              {visibleRegions.map((region) => {
                if (region.region_type === "TABLE" && region.content_html) {
                  return (
                    <div key={region.id} className="my-4 overflow-x-auto rounded-lg border border-gray-200 p-2 bg-gray-50">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 mb-2 px-1">
                        <TableIcon className="h-4 w-4 text-indigo-600" />
                        <span>Source Table</span>
                      </div>
                      <div dangerouslySetInnerHTML={{ __html: region.content_html }} />
                    </div>
                  );
                }

                if (region.region_type === "IMAGE" && region.media_path) {
                  return (
                    <div key={region.id} className="my-4 flex flex-col items-center">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={`http://localhost:8000${region.media_path}`}
                        alt="Source diagram"
                        className="max-h-96 rounded-lg border border-gray-200 shadow-sm object-contain"
                      />
                      <span className="mt-1 text-[11px] text-gray-500">Source Diagram / Image</span>
                    </div>
                  );
                }

                return (
                  <div key={region.id} className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
                    {region.content_text}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
