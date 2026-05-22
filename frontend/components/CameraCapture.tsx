"use client";

import { useEffect } from "react";
import { Camera, RotateCcw, CheckCircle2 } from "lucide-react";

import { useCamera } from "@/hooks/useCamera";

interface CameraCaptureProps {
  active: boolean;
  onConfirm: (blob: Blob) => void | Promise<void>;
}

export default function CameraCapture({
  active,
  onConfirm,
}: CameraCaptureProps) {
  const {
    videoRef,
    isSupported,
    isStarting,
    isStreaming,
    permissionError,
    capturedBlob,
    capturedDataUrl,
    startCamera,
    stopCamera,
    capture,
    retake,
  } = useCamera();

  useEffect(() => {
    if (active) {
      void startCamera();
    } else {
      stopCamera();
    }
  }, [active, startCamera, stopCamera]);

  if (!isSupported) {
    return (
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
        Trinh duyet khong ho tro MediaDevices API.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-black">
        {capturedDataUrl ? (
          <img
            src={capturedDataUrl}
            alt="Anh chup tu camera"
            className="aspect-4/3 w-full object-cover"
          />
        ) : (
          <video
            ref={videoRef}
            muted
            playsInline
            className="aspect-4/3 w-full object-cover"
          />
        )}
      </div>

      {permissionError ? (
        <p className="text-sm text-red-600">{permissionError}</p>
      ) : null}

      {!capturedDataUrl ? (
        <div className="flex justify-center">
          <button
            type="button"
            disabled={!isStreaming || isStarting}
            onClick={() => void capture()}
            className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-blue-700 text-white disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Chup"
          >
            <Camera className="h-6 w-6" />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => void retake()}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
          >
            <RotateCcw className="h-4 w-4" />
            Chup lai
          </button>
          <button
            type="button"
            onClick={() => {
              if (capturedBlob) {
                void onConfirm(capturedBlob);
              }
            }}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white"
          >
            <CheckCircle2 className="h-4 w-4" />
            Dung anh nay
          </button>
        </div>
      )}
    </div>
  );
}
