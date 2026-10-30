"use client";

import React, { useState } from "react";
import { Topic, TopicContentView } from "@/types";
import { Tag, Search, Copy, Check, BookOpen } from "lucide-react";

interface TopicKeywordsViewProps {
  topic: Topic;
  content: TopicContentView;
}

export default function TopicKeywordsView({ topic, content }: TopicKeywordsViewProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const rawKeywords = content.learning_data?.keywords || topic.learning_data?.keywords || [];
  const keywords = rawKeywords.map((k: any) => ({
    keyword: k.keyword || k.term || "Keyword",
    explanation: k.explanation || k.definition || "",
    source_reference: k.source_reference || k.source_ref,
  }));

  const filteredKeywords = keywords.filter((k) =>
    k.keyword.toLowerCase().includes(searchTerm.toLowerCase()) ||
    k.explanation.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCopy = (keyword: string, explanation: string, idx: number) => {
    navigator.clipboard.writeText(`${keyword}: ${explanation}`);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Important Key Words</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Key concepts, definitions, and technical vocabulary for this topic.
          </p>
        </div>

        {/* Search input */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Filter keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-gray-50 pl-9 pr-4 py-2 text-xs focus:bg-white focus:border-indigo-500 focus:outline-none transition-colors"
          />
        </div>
      </div>

      {filteredKeywords.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-gray-200 bg-white p-12 text-center">
          <Tag className="h-8 w-8 text-gray-300 mx-auto mb-2" />
          <p className="text-xs text-gray-500">
            {searchTerm ? "No keywords match your search query." : "No explicit keywords cataloged for this topic."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredKeywords.map((item, idx) => (
            <div
              key={idx}
              className="group relative flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-2xs hover:border-indigo-300 hover:shadow-sm transition-all"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
                      <Tag className="h-3 w-3" />
                    </span>
                    <h3 className="font-bold text-gray-900 text-sm">{item.keyword}</h3>
                  </div>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed pl-8">{item.explanation}</p>
              </div>

              <div className="mt-4 flex items-center justify-end pt-2 border-t border-gray-50">
                <button
                  onClick={() => handleCopy(item.keyword, item.explanation, idx)}
                  className="flex items-center gap-1 text-[11px] font-semibold text-gray-400 hover:text-indigo-600 transition-colors"
                >
                  {copiedIndex === idx ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy Definition</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
