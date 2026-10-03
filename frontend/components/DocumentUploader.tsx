"use client";

import { useState, useRef } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { DocumentInfo } from "@/types";
import { formatBytes } from "@/lib/utils";

interface DocumentUploaderProps {
  unitId: string;
  existingDocument?: DocumentInfo;
  onUploadSuccess: (doc: DocumentInfo) => void;
}

export default function DocumentUploader({
  unitId,
  existingDocument,
  onUploadSuccess,
}: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setError(null);
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'pptx', 'docx'].includes(ext || '')) {
      setError("Unsupported file format. Please upload a .pdf, .pptx, or .docx file.");
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setError("File exceeds maximum allowed size (50MB).");
      return;
    }

    setIsUploading(true);
    try {
      const doc = await api.uploadDocument(unitId, file);
      onUploadSuccess(doc);
    } catch (err: any) {
      setError(err.message || "Failed to upload and process document.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="w-full">
      {existingDocument ? (
        <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold text-gray-900 text-sm">{existingDocument.file_name}</p>
                <span className="rounded bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
                  {existingDocument.file_type}
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {formatBytes(existingDocument.file_size)} •{" "}
                {existingDocument.page_count
                  ? `${existingDocument.page_count} pages`
                  : existingDocument.slide_count
                  ? `${existingDocument.slide_count} slides`
                  : "Processed"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
                existingDocument.processing_status === "PROCESSED"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : existingDocument.processing_status === "REVIEW_REQUIRED"
                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                  : "bg-red-50 text-red-700 border border-red-200"
              }`}
            >
              {existingDocument.processing_status === "PROCESSED" ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Source Verified
                </>
              ) : existingDocument.processing_status === "REVIEW_REQUIRED" ? (
                <>
                  <AlertCircle className="h-3.5 w-3.5" />
                  Review Required
                </>
              ) : (
                <>
                  <AlertCircle className="h-3.5 w-3.5" />
                  Processing Failed
                </>
              )}
            </span>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 underline"
            >
              Replace
            </button>
          </div>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`group flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? "border-indigo-500 bg-indigo-50/50"
              : "border-gray-300 hover:border-indigo-400 bg-gray-50/50 hover:bg-gray-50"
          }`}
        >
          {isUploading ? (
            <div className="flex flex-col items-center gap-3 py-4">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
              <div>
                <p className="font-semibold text-gray-800 text-sm">Processing source document...</p>
                <p className="text-xs text-gray-500 mt-1">
                  Extracting native headings, text, layouts, images, and tables with source fidelity.
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 transition-transform group-hover:scale-110 mb-3">
                <UploadCloud className="h-6 w-6" />
              </div>
              <p className="text-sm font-semibold text-gray-800">
                Click to upload or drag & drop the Unit resource
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Supports PDF, PPTX, or DOCX (up to 50MB)
              </p>
              <div className="mt-3 flex gap-2">
                <span className="rounded bg-gray-200 px-2 py-0.5 text-[11px] font-medium text-gray-700">.pdf</span>
                <span className="rounded bg-gray-200 px-2 py-0.5 text-[11px] font-medium text-gray-700">.pptx</span>
                <span className="rounded bg-gray-200 px-2 py-0.5 text-[11px] font-medium text-gray-700">.docx</span>
              </div>
            </>
          )}
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.pptx,.docx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
          }
        }}
      />

      {error && (
        <div className="mt-3 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
