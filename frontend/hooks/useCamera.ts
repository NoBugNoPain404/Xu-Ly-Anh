"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseCameraResult {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  isSupported: boolean;
  isStarting: boolean;
  isStreaming: boolean;
  permissionError: string | null;
  capturedBlob: Blob | null;
  capturedDataUrl: string | null;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
  capture: () => Promise<void>;
  retake: () => Promise<void>;
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () =>
      reject(new Error("Khong the doc anh chup tu camera."));
    reader.readAsDataURL(blob);
  });
}

export function useCamera(): UseCameraResult {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isStarting, setIsStarting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [capturedDataUrl, setCapturedDataUrl] = useState<string | null>(null);

  const isSupported =
    typeof navigator !== "undefined" &&
    Boolean(navigator.mediaDevices?.getUserMedia);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) {
        track.stop();
      }
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsStreaming(false);
  }, []);

  const startCamera = useCallback(async () => {
    if (!isSupported) {
      setPermissionError("Trinh duyet khong ho tro MediaDevices API.");
      return;
    }

    setIsStarting(true);
    setPermissionError(null);

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
        },
        audio: false,
      });

      streamRef.current = mediaStream;

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play();
      }

      setIsStreaming(true);
    } catch {
      setPermissionError(
        "Khong the truy cap camera. Vui long cap quyen camera va thu lai.",
      );
      stopCamera();
    } finally {
      setIsStarting(false);
    }
  }, [isSupported, stopCamera]);

  const capture = useCallback(async () => {
    const video = videoRef.current;
    if (!video || !isStreaming) {
      return;
    }

    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    ctx.drawImage(video, 0, 0, width, height);

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.92);
    });

    if (!blob) {
      return;
    }

    const dataUrl = await blobToDataUrl(blob);

    setCapturedBlob(blob);
    setCapturedDataUrl(dataUrl);

    stopCamera();
  }, [isStreaming, stopCamera]);

  const retake = useCallback(async () => {
    setCapturedBlob(null);
    setCapturedDataUrl(null);
    await startCamera();
  }, [startCamera]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return {
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
  };
}
