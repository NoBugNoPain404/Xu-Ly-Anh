"use client";

import { X } from "lucide-react";

import type { FileMeta } from "@/types/cccd";

interface ImagePreviewProps {
  previewDataUrl: string;
  fileMeta: FileMeta | null;
  valid: boolean;
  errorMessage: string | null;
  onRemove: () => void;
  compressionProgress: number;
}

function formatSize(size: number): string {
  if (size >= 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  }
  return `${(size / 1024).toFixed(2)} KB`;
}

export default function ImagePreview({
  previewDataUrl,
  fileMeta,
  valid,
  errorMessage,
  onRemove,
  compressionProgress,
}: ImagePreviewProps) {
  return (
    <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-slate-100">
        <img
          src={previewDataUrl}
          alt="Xem truoc anh CCCD"
          className="aspect-4/3 w-full object-contain"
        />
        <button
          type="button"
          onClick={onRemove}
          className="absolute right-2 top-2 rounded-full bg-black/70 p-1 text-white"
          aria-label="Xoa anh"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {fileMeta ? (
        <div className="space-y-1 text-sm text-slate-700">
          <p>
            <span className="font-semibold">Ten file:</span> {fileMeta.name}
          </p>
          <p>
            <span className="font-semibold">Kich thuoc:</span>{" "}
            {formatSize(fileMeta.size)}
          </p>
          <p>
            <span className="font-semibold">Dinh dang:</span>{" "}
            {fileMeta.type || fileMeta.extension}
          </p>
        </div>
      ) : null}

      <div>
        {valid ? (
          <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
            Da xac thuc
          </span>
        ) : (
          <span className="inline-flex rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700">
            Khong hop le
          </span>
        )}
      </div>

      {errorMessage ? (
        <p className="text-sm text-red-600">{errorMessage}</p>
      ) : null}

      {compressionProgress > 0 && compressionProgress < 100 ? (
        <div className="space-y-1">
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full bg-blue-700 transition-all"
              style={{ width: `${compressionProgress}%` }}
            />
          </div>
          <p className="text-xs text-slate-500">
            Dang nen anh: {Math.round(compressionProgress)}%
          </p>
        </div>
      ) : null}
    </section>
  );
}
