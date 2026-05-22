"use client";

import type { CccdResult } from "@/types/cccd";

interface ResultCardProps {
  result: CccdResult;
  onDownloadJson: () => void;
  onRescan: () => void;
}

interface ResultRowProps {
  label: string;
  value: string;
  strong?: boolean;
}

function ResultRow({ label, value, strong }: ResultRowProps) {
  return (
    <div className="grid grid-cols-3 gap-3 border-b border-slate-100 py-2 text-sm">
      <p className="col-span-1 text-slate-500">{label}</p>
      <p
        className={`col-span-2 text-slate-900 ${strong ? "font-bold" : "font-medium"}`}
      >
        {value || "-"}
      </p>
    </div>
  );
}

export default function ResultCard({
  result,
  onDownloadJson,
  onRescan,
}: ResultCardProps) {
  return (
    <section className="space-y-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
      <h2 className="text-base font-bold text-emerald-900">
        Ket qua quet CCCD
      </h2>

      <div className="rounded-lg bg-white p-3">
        <ResultRow label="So CCCD" value={result.soCccd} strong />
        <ResultRow label="Ho va ten" value={result.hoVaTen} />
        <ResultRow label="Ngay sinh" value={result.ngaySinh} />
        <ResultRow label="Gioi tinh" value={result.gioiTinh} />
        <ResultRow label="Quoc tich" value={result.quocTich} />
        <ResultRow label="Que quan" value={result.queQuan} />
        <ResultRow label="Noi thuong tru" value={result.noiThuongTru} />
        <ResultRow label="Ngay cap" value={result.ngayCap} />
        <ResultRow label="Co gia tri den" value={result.coGiaTriDen} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={onDownloadJson}
          className="rounded-lg border border-emerald-700 bg-white px-4 py-2 text-sm font-semibold text-emerald-700"
        >
          Tai xuong JSON
        </button>
        <button
          type="button"
          onClick={onRescan}
          className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white"
        >
          Quet tiep
        </button>
      </div>
    </section>
  );
}
