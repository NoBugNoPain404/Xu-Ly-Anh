"use client";

import { Upload, Camera } from "lucide-react";
import * as Tabs from "@radix-ui/react-tabs";
import { useRef, useState } from "react";

interface UploadZoneProps {
  mode: "upload" | "camera";
  onModeChange: (mode: "upload" | "camera") => void;
  onFileSelected: (file: File) => void | Promise<void>;
  cameraContent: React.ReactNode;
}

export default function UploadZone({
  mode,
  onModeChange,
  onFileSelected,
  cameraContent,
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (fileList: FileList | null) => {
    const file = fileList?.[0];
    if (!file) {
      return;
    }
    onFileSelected(file);
  };

  return (
    <Tabs.Root
      value={mode}
      onValueChange={(value) => onModeChange(value as "upload" | "camera")}
      className="space-y-4"
    >
      <Tabs.List className="grid grid-cols-2 rounded-xl bg-slate-100 p-1">
        <Tabs.Trigger
          value="upload"
          className="inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 data-[state=active]:bg-white data-[state=active]:text-blue-700"
        >
          <Upload className="h-4 w-4" />
          Tai len anh
        </Tabs.Trigger>
        <Tabs.Trigger
          value="camera"
          className="inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 data-[state=active]:bg-white data-[state=active]:text-blue-700"
        >
          <Camera className="h-4 w-4" />
          Chup anh
        </Tabs.Trigger>
      </Tabs.List>

      <Tabs.Content value="upload" className="space-y-3">
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setIsDragging(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            handleFiles(event.dataTransfer.files);
          }}
          className={`rounded-xl border-2 border-dashed p-6 text-center transition ${
            isDragging
              ? "border-blue-500 bg-blue-50"
              : "border-blue-300 bg-white hover:bg-slate-50"
          }`}
        >
          <Upload className="mx-auto mb-3 h-8 w-8 text-blue-600" />
          <p className="text-sm font-medium text-slate-700">
            Keo va tha anh vao day hoac nhan de chon
          </p>
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              inputRef.current?.click();
            }}
            className="mt-4 rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
          >
            Chon anh tu may tinh
          </button>
          <p className="mt-3 text-xs text-slate-500">
            Dinh dang: JPG, PNG, WEBP, BMP, HEIC
          </p>
          <p className="text-xs text-slate-500">Kich thuoc toi da: 10 MB</p>
        </div>

        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".jpg,.jpeg,.png,.webp,.bmp,.heic,image/jpeg,image/png,image/webp,image/bmp,image/heic,image/heif"
          onChange={(event) => handleFiles(event.currentTarget.files)}
        />
      </Tabs.Content>

      <Tabs.Content value="camera">{cameraContent}</Tabs.Content>
    </Tabs.Root>
  );
}
