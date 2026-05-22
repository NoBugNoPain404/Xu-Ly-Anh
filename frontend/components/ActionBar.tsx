"use client";

import { LoaderCircle } from "lucide-react";

interface ActionBarProps {
  canStart: boolean;
  isLoading: boolean;
  showReset: boolean;
  onStart: () => void | Promise<void>;
  onReset: () => void;
}

export default function ActionBar({
  canStart,
  isLoading,
  showReset,
  onStart,
  onReset,
}: ActionBarProps) {
  return (
    <div className="space-y-3">
      <button
        type="button"
        disabled={!canStart || isLoading}
        onClick={() => void onStart()}
        className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-blue-900 px-4 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? (
          <>
            <LoaderCircle className="h-4 w-4 animate-spin" />
            Dang xu ly...
          </>
        ) : (
          "Bat dau quet"
        )}
      </button>

      {showReset ? (
        <button
          type="button"
          onClick={onReset}
          className="w-full rounded-lg border border-slate-300 bg-transparent px-4 py-3 text-sm font-semibold text-slate-700"
        >
          Lam lai
        </button>
      ) : null}
    </div>
  );
}
