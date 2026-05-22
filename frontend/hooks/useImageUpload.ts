"use client";

import { useState } from "react";

import { validateImage, validateImageFromCamera } from "@/lib/imageValidator";
import type { FileMeta } from "@/types/cccd";

type UploadValidationState =
  | "idle"
  | "file_selected"
  | "validation_error"
  | "ready";

interface UseImageUploadState {
  selectedFile: File | null;
  validatedFile: File | null;
  fileMeta: FileMeta | null;
  previewDataUrl: string | null;
  validationError: string | null;
  validationState: UploadValidationState;
  compressionProgress: number;
}

const initialState: UseImageUploadState = {
  selectedFile: null,
  validatedFile: null,
  fileMeta: null,
  previewDataUrl: null,
  validationError: null,
  validationState: "idle",
  compressionProgress: 0,
};

async function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () =>
      reject(new Error("Khong the doc file de xem truoc."));
    reader.readAsDataURL(file);
  });
}

export function useImageUpload() {
  const [state, setState] = useState<UseImageUploadState>(initialState);

  const clear = () => {
    setState(initialState);
  };

  const validateFile = async (file: File, isCamera: boolean) => {
    setState((prev) => ({
      ...prev,
      selectedFile: file,
      validatedFile: null,
      validationError: null,
      validationState: "file_selected",
      compressionProgress: 0,
    }));

    const previewDataUrl = await fileToDataUrl(file);
    setState((prev) => ({
      ...prev,
      previewDataUrl,
    }));

    try {
      const validationResult = isCamera
        ? await validateImageFromCamera(file, {
            onCompressionProgress: (progress) => {
              setState((prev) => ({
                ...prev,
                compressionProgress: progress,
              }));
            },
          })
        : await validateImage(file, {
            onCompressionProgress: (progress) => {
              setState((prev) => ({
                ...prev,
                compressionProgress: progress,
              }));
            },
          });

      const validatedPreview = await fileToDataUrl(validationResult.file);

      setState((prev) => ({
        ...prev,
        validatedFile: validationResult.file,
        fileMeta: validationResult.meta,
        previewDataUrl: validatedPreview,
        validationState: "ready",
        validationError: null,
        compressionProgress: validationResult.compressed
          ? 100
          : prev.compressionProgress,
      }));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Khong the xac thuc anh da chon.";

      setState((prev) => ({
        ...prev,
        validatedFile: null,
        fileMeta: {
          name: file.name,
          size: file.size,
          type: file.type,
          extension: file.name.includes(".")
            ? file.name.slice(file.name.lastIndexOf(".")).toLowerCase()
            : "",
        },
        validationState: "validation_error",
        validationError: message,
      }));
    }
  };

  const selectUploadFile = async (file: File) => {
    await validateFile(file, false);
  };

  const selectCameraFile = async (blob: Blob) => {
    const cameraFile = new File([blob], "camera_capture.jpg", {
      type: "image/jpeg",
      lastModified: Date.now(),
    });

    await validateFile(cameraFile, true);
  };

  return {
    ...state,
    isValid: state.validationState === "ready" && Boolean(state.validatedFile),
    selectUploadFile,
    selectCameraFile,
    clear,
  };
}
