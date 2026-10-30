"use client";

import React, { useState } from "react";
import { TopicContentView, SourceRegion } from "@/types";
import {
  Image as ImageIcon,
  ZoomIn,
  X,
  FileText,
  Table as TableIcon,
  Maximize2,
  ExternalLink,
  Layers,
} from "lucide-react";

interface TopicVisualsGalleryProps {
  content: TopicContentView;
}

export default function TopicVisualsGallery({ content }: TopicVisualsGalleryProps) {
  const [selectedVisual, setSelectedVisual] = useState<SourceRegion | null>(null);

  // Filter regions that are visuals (IMAGE, DIAGRAM, FLOWCHART, TABLE, SLIDE, FULL_PAGE)
  const visualRegions = content.regions.filter((r) =>
    ["IMAGE", "DIAGRAM", "FLOWCHART", "TABLE", "EQUATION"].includes(r.region_type)
  );

  const getMediaUrl = (path?: string) => {
    if (!path) return "";
    if (path.startsWith("http://") || path.startsWith("https://")) return path;
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    const host = apiBase.replace(/\/api\/?$/, "");
    return `${host}${path.startsWith("/") ? "" : "/"}${path}`;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header Info */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Topic Diagrams</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Authentic diagrams, figures, and charts extracted directly from the study material for this topic.
            </p>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 border border-emerald-200 self-start sm:self-auto">
            {visualRegions.length} {visualRegions.length === 1 ? "Diagram" : "Diagrams"}
          </span>
        </div>
      </div>

      {visualRegions.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-gray-200 bg-white p-12 text-center">
          <ImageIcon className="h-10 w-10 text-gray-300 mx-auto mb-3" />
          <h3 className="font-bold text-gray-800 text-sm">No diagrams provided for this topic in the study material</h3>
          <p className="mt-1 text-xs text-gray-500 max-w-md mx-auto">
            This topic consists of comprehensive notes, key concepts, definitions, and questions. Diagrams are displayed whenever provided in the original files.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {visualRegions.map((region, idx) => {
            const hasMedia = !!region.media_path;
            const mediaUrl = getMediaUrl(region.media_path);

            return (
              <div
                key={region.id || idx}
                className="group relative flex flex-col rounded-2xl border border-gray-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-all"
              >
                {/* Visual Header */}
                <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/80 px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    {region.region_type === "TABLE" ? (
                      <TableIcon className="h-4 w-4 text-emerald-600" />
                    ) : (
                      <ImageIcon className="h-4 w-4 text-indigo-600" />
                    )}
                    <span className="text-xs font-bold text-gray-800">
                      {region.region_type === "TABLE"
                        ? "Data Table"
                        : region.region_type === "FLOWCHART"
                        ? "Flowchart"
                        : region.region_type === "DIAGRAM"
                        ? "Diagram"
                        : "Topic Diagram"}
                    </span>
                  </div>
                  <span className="rounded-md bg-white px-2 py-0.5 text-[10px] font-bold text-gray-600 border border-gray-200 shadow-2xs">
                    Figure {idx + 1}
                  </span>
                </div>

                {/* Visual Content Body */}
                <div className="relative flex min-h-60 max-h-96 items-center justify-center bg-gray-950/5 p-4 overflow-hidden">
                  {hasMedia ? (
                    <div
                      onClick={() => setSelectedVisual(region)}
                      className="cursor-zoom-in group/img relative flex h-full w-full items-center justify-center"
                    >
                      <img
                        src={mediaUrl}
                        alt="Topic Diagram"
                        className="max-h-80 w-auto rounded-lg object-contain transition-transform group-hover/img:scale-[1.02]"
                        loading="lazy"
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity group-hover/img:opacity-100 rounded-lg">
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1.5 text-xs font-bold text-gray-900 shadow-lg">
                          <ZoomIn className="h-3.5 w-3.5" />
                          Click to Expand
                        </span>
                      </div>
                    </div>
                  ) : region.content_html ? (
                    <div
                      className="w-full overflow-x-auto text-xs"
                      dangerouslySetInnerHTML={{ __html: region.content_html }}
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center p-6 text-center text-gray-400">
                      <FileText className="h-8 w-8 mb-2" />
                      <p className="text-xs font-semibold">Visual content detected</p>
                    </div>
                  )}
                </div>

                {/* Footer Notes / Content */}
                <div className="border-t border-gray-100 bg-white p-4">
                  {region.content_text && (
                    <p className="text-xs text-gray-600 line-clamp-3 leading-relaxed bg-gray-50 p-2.5 rounded-lg border border-gray-100">
                      <span className="font-bold text-gray-700">Description: </span>
                      {region.content_text.replace(/\s*\([^)]*slide[^)]*\)/gi, "").trim()}
                    </p>
                  )}
                  {hasMedia && (
                    <button
                      onClick={() => setSelectedVisual(region)}
                      className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-800"
                    >
                      <Maximize2 className="h-3.5 w-3.5" />
                      <span>Inspect High Resolution</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Expanded Modal */}
      {selectedVisual && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="relative flex max-h-[90vh] max-w-5xl w-full flex-col rounded-2xl bg-white shadow-2xl overflow-hidden border border-gray-200">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
              <div>
                <h3 className="font-bold text-gray-900 text-sm">
                  {selectedVisual.region_type} Viewer
                </h3>
                <p className="text-xs text-gray-500">
                  {selectedVisual.source_reference || (selectedVisual.slide_number ? `Slide ${selectedVisual.slide_number}` : selectedVisual.page_number ? `Page ${selectedVisual.page_number}` : "Source Visual")}
                </p>
              </div>
              <button
                onClick={() => setSelectedVisual(null)}
                className="rounded-xl p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Image Display */}
            <div className="flex flex-1 items-center justify-center overflow-auto bg-gray-950 p-6 min-h-[50vh]">
              {selectedVisual.media_path ? (
                <img
                  src={getMediaUrl(selectedVisual.media_path)}
                  alt="Expanded source visual"
                  className="max-h-[70vh] w-auto max-w-full rounded-lg object-contain shadow-md"
                />
              ) : selectedVisual.content_html ? (
                <div
                  className="w-full bg-white p-6 rounded-lg overflow-auto"
                  dangerouslySetInnerHTML={{ __html: selectedVisual.content_html }}
                />
              ) : null}
            </div>

            {/* Modal Footer */}
            {selectedVisual.content_text && (
              <div className="border-t border-gray-200 bg-gray-50 px-6 py-3 text-xs text-gray-700">
                <span className="font-bold">Extracted Context: </span>
                {selectedVisual.content_text}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
