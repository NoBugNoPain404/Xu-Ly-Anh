import imageCompression from "browser-image-compression";

import type { FileMeta, ValidationSuccess } from "@/types/cccd";

const MIN_SIZE_BYTES = 10 * 1024;
const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const COMPRESS_THRESHOLD_BYTES = 2 * 1024 * 1024;
const COMPRESS_TARGET_MB = 1.5;

const ACCEPTED_MIME_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/bmp",
  "image/heic",
  "image/heif",
]);

const ACCEPTED_EXTENSIONS = new Set([
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
  ".bmp",
  ".heic",
]);

const FORMAT_ERROR =
  "Dinh dang khong duoc ho tro. Vui long chon anh JPEG, PNG, WEBP hoac BMP.";
const MAGIC_BYTES_ERROR =
  "File bi gia mao hoac khong dung dinh dang anh hop le.";
const TOO_LARGE_ERROR = "File qua lon (toi da 10MB)";
const TOO_SMALL_ERROR = "File qua nho";
const COMPRESSION_ERROR = "Nen anh that bai. Vui long thu lai.";

export interface ValidateImageOptions {
  skipExtensionCheck?: boolean;
  onCompressionProgress?: (progress: number) => void;
}

function getExtension(fileName: string): string {
  const index = fileName.lastIndexOf(".");
  if (index < 0) {
    return "";
  }

  return fileName.slice(index).toLowerCase();
}

function hasPngSignature(bytes: Uint8Array): boolean {
  return (
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47
  );
}

function hasJpegSignature(bytes: Uint8Array): boolean {
  return bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
}

function hasWebpSignature(bytes: Uint8Array): boolean {
  return (
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46 &&
    bytes[8] === 0x57 &&
    bytes[9] === 0x45 &&
    bytes[10] === 0x42 &&
    bytes[11] === 0x50
  );
}

function hasBmpSignature(bytes: Uint8Array): boolean {
  return bytes[0] === 0x42 && bytes[1] === 0x4d;
}

function hasHeicHeifSignature(bytes: Uint8Array): boolean {
  return (
    bytes[4] === 0x66 &&
    bytes[5] === 0x74 &&
    bytes[6] === 0x79 &&
    bytes[7] === 0x70
  );
}

async function readMagicBytes(file: File): Promise<Uint8Array> {
  const buffer = await file.slice(0, 12).arrayBuffer();
  return new Uint8Array(buffer);
}

function validateMime(file: File): void {
  if (!ACCEPTED_MIME_TYPES.has(file.type)) {
    throw new Error(FORMAT_ERROR);
  }
}

function validateExtension(file: File, skipExtensionCheck: boolean): string {
  const extension = getExtension(file.name);

  if (!skipExtensionCheck && !ACCEPTED_EXTENSIONS.has(extension)) {
    throw new Error(FORMAT_ERROR);
  }

  return extension;
}

function validateMagicBytes(bytes: Uint8Array): void {
  const valid =
    hasJpegSignature(bytes) ||
    hasPngSignature(bytes) ||
    hasWebpSignature(bytes) ||
    hasBmpSignature(bytes) ||
    hasHeicHeifSignature(bytes);

  if (!valid) {
    throw new Error(MAGIC_BYTES_ERROR);
  }
}

function validateSize(file: File): void {
  if (file.size > MAX_SIZE_BYTES) {
    throw new Error(TOO_LARGE_ERROR);
  }

  if (file.size < MIN_SIZE_BYTES) {
    throw new Error(TOO_SMALL_ERROR);
  }
}

function buildMeta(file: File, extension: string): FileMeta {
  return {
    name: file.name,
    size: file.size,
    type: file.type,
    extension,
  };
}

async function maybeCompressImage(
  file: File,
  onCompressionProgress?: (progress: number) => void,
): Promise<{ file: File; compressed: boolean }> {
  if (file.size <= COMPRESS_THRESHOLD_BYTES) {
    return { file, compressed: false };
  }

  try {
    const compressedBlob = await imageCompression(file, {
      maxSizeMB: COMPRESS_TARGET_MB,
      useWebWorker: true,
      onProgress: (progress) => {
        onCompressionProgress?.(progress);
      },
      preserveExif: false,
    });

    const compressedFile = new File([compressedBlob], file.name, {
      type: compressedBlob.type || file.type,
      lastModified: Date.now(),
    });

    return { file: compressedFile, compressed: true };
  } catch {
    throw new Error(COMPRESSION_ERROR);
  }
}

export async function validateImage(
  file: File,
  options: ValidateImageOptions = {},
): Promise<ValidationSuccess> {
  validateMime(file);
  const extension = validateExtension(
    file,
    Boolean(options.skipExtensionCheck),
  );
  const magicBytes = await readMagicBytes(file);
  validateMagicBytes(magicBytes);
  validateSize(file);

  const compressionResult = await maybeCompressImage(
    file,
    options.onCompressionProgress,
  );

  const finalExtension = getExtension(compressionResult.file.name) || extension;

  return {
    valid: true,
    file: compressionResult.file,
    compressed: compressionResult.compressed,
    meta: buildMeta(compressionResult.file, finalExtension),
  };
}

export async function validateImageFromCamera(
  blob: Blob,
  options: ValidateImageOptions = {},
): Promise<ValidationSuccess> {
  const file = new File([blob], "camera_capture.jpg", {
    type: "image/jpeg",
    lastModified: Date.now(),
  });

  return validateImage(file, {
    ...options,
    skipExtensionCheck: true,
  });
}
