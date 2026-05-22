"use client";

import { useEffect, useMemo, useState } from "react";
import { ShieldCheck, Wifi, WifiOff } from "lucide-react";

import ActionBar from "@/components/ActionBar";
import CameraCapture from "@/components/CameraCapture";
import ImagePreview from "@/components/ImagePreview";
import ResultCard from "@/components/ResultCard";
import UploadZone from "@/components/UploadZone";
import { useImageUpload } from "@/hooks/useImageUpload";
import { ApiClientError, scanCccd } from "@/lib/apiClient";
import type { CccdResult, ScannerUiState } from "@/types/cccd";

type ScanRequestState = "idle" | "loading" | "success" | "error";

export default function Home() {
  const [mode, setMode] = useState<"upload" | "camera">("upload");
  const upload = useImageUpload();

  const [scanState, setScanState] = useState<ScanRequestState>("idle");
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<CccdResult | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );

  const uiState: ScannerUiState = useMemo(() => {
    if (scanState === "loading") {
      return "loading";
    }

    if (scanState === "success") {
      return "success";
    }

    if (scanState === "error") {
      return "error";
    }

    return upload.validationState;
  }, [scanState, upload.validationState]);

  useEffect(() => {
    const setOnline = () => setIsOnline(true);
    const setOffline = () => setIsOnline(false);

    window.addEventListener("online", setOnline);
    window.addEventListener("offline", setOffline);

    return () => {
      window.removeEventListener("online", setOnline);
      window.removeEventListener("offline", setOffline);
    };
  }, []);

  useEffect(() => {
    if (!toastMessage) {
      return;
    }

    const timeout = setTimeout(() => {
      setToastMessage(null);
    }, 2500);

    return () => clearTimeout(timeout);
  }, [toastMessage]);

  const resetAll = () => {
    upload.clear();
    setScanState("idle");
    setScanError(null);
    setScanResult(null);
    setToastMessage(null);
  };

  const handleModeChange = (nextMode: "upload" | "camera") => {
    setMode(nextMode);
    resetAll();
  };

  const handleUploadFile = async (file: File) => {
    setScanState("idle");
    setScanError(null);
    setScanResult(null);
    await upload.selectUploadFile(file);
  };

  const handleCameraConfirm = async (blob: Blob) => {
    setScanState("idle");
    setScanError(null);
    setScanResult(null);
    await upload.selectCameraFile(blob);
  };

  const handleStartScan = async () => {
    if (!upload.validatedFile) {
      return;
    }

    setScanState("loading");
    setScanError(null);

    try {
      const result = await scanCccd(upload.validatedFile);
      setScanResult(result);
      setScanState("success");
      setToastMessage("Quet thanh cong!");
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : "Khong the xu ly yeu cau quet CCCD.";

      setScanState("error");
      setScanError(message);
    }
  };

  const handleDownloadJson = () => {
    if (!scanResult) {
      return;
    }

    const blob = new Blob([JSON.stringify(scanResult, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "cccd-result.json";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-linear-to-b from-sky-50 via-white to-slate-50 px-4 py-6 sm:px-6">
      <main className="mx-auto w-full max-w-180 space-y-5">
        <header className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-blue-100 p-2 text-blue-700">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  CCCD Card Information Scanner
                </p>
                <h1 className="text-lg font-bold text-slate-900">
                  Quet thong tin CCCD
                </h1>
              </div>
            </div>

            <span
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
                isOnline
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-slate-200 text-slate-600"
              }`}
            >
              {isOnline ? (
                <Wifi className="h-3.5 w-3.5" />
              ) : (
                <WifiOff className="h-3.5 w-3.5" />
              )}
              {isOnline ? "Online" : "Offline"}
            </span>
          </div>
        </header>

        {toastMessage ? (
          <div className="rounded-lg border border-emerald-300 bg-emerald-100 px-4 py-2 text-sm font-semibold text-emerald-800">
            {toastMessage}
          </div>
        ) : null}

        <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <UploadZone
            mode={mode}
            onModeChange={handleModeChange}
            onFileSelected={handleUploadFile}
            cameraContent={
              <CameraCapture
                active={mode === "camera"}
                onConfirm={handleCameraConfirm}
              />
            }
          />

          {upload.previewDataUrl ? (
            <ImagePreview
              previewDataUrl={upload.previewDataUrl}
              fileMeta={upload.fileMeta}
              valid={upload.isValid}
              errorMessage={upload.validationError}
              onRemove={resetAll}
              compressionProgress={upload.compressionProgress}
            />
          ) : null}

          <ActionBar
            canStart={upload.isValid}
            isLoading={uiState === "loading"}
            showReset={scanState === "success" || scanState === "error"}
            onStart={handleStartScan}
            onReset={resetAll}
          />
        </section>

        {uiState === "error" && scanError ? (
          <section className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {scanError}
          </section>
        ) : null}

        {scanResult && uiState === "success" ? (
          <ResultCard
            result={scanResult}
            onDownloadJson={handleDownloadJson}
            onRescan={resetAll}
          />
        ) : null}

        <footer className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600">
          <p>Anh cua ban duoc xu ly tuc thi va khong duoc luu tru.</p>
          <p className="mt-1">Phien ban giao dien: 1.0.0</p>
        </footer>
      </main>
    </div>
  );
}
