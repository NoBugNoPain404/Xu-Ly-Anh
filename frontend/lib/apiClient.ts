import type { CccdResult } from "@/types/cccd";

// ✅ FIX: dùng base URL rõ ràng
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const API_ENDPOINT = `${API_BASE_URL}/api/v1/scan`;
const API_TIMEOUT_MS = 30_000;

const ERROR_MESSAGES: Record<number, string> = {
  400: "Khong the doc thong tin tu anh. Vui long chup lai ro hon.",
  413: "File vuot qua gioi han cho phep cua server.",
  422: "Khong tim thay the CCCD trong anh hoac file khong hop le.",
  429: "Qua so luong yeu cau. Vui long thu lai sau it phut.",
  500: "He thong dang gap su co. Vui long thu lai sau.",
};

const TIMEOUT_MESSAGE = "Ket noi qua lau. Kiem tra mang va thu lai.";
const UNKNOWN_ERROR_MESSAGE = "Khong the ket noi den he thong quet CCCD.";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

function toDisplayDate(input: unknown): string {
  if (typeof input !== "string" || !input.trim()) return "";

  if (/^\d{2}\/\d{2}\/\d{4}$/.test(input)) return input;

  if (/^\d{4}-\d{2}-\d{2}/.test(input)) {
    const [y, m, d] = input.slice(0, 10).split("-");
    return `${d}/${m}/${y}`;
  }

  return input;
}

function readString(
  data: Record<string, unknown>,
  keys: string[],
  fallback = "",
): string {
  for (const key of keys) {
    const value = data[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return fallback;
}

function mapResponseToCccd(data: Record<string, unknown>): CccdResult {
  return {
    soCccd: readString(data, ["so_cccd", "soCccd", "id_number", "cccd_number"]),
    hoVaTen: readString(data, ["ho_va_ten", "hoVaTen", "full_name", "name"]),
    ngaySinh: toDisplayDate(
      readString(data, [
        "ngay_sinh",
        "ngaySinh",
        "dob",
        "birth_date",
        "date_of_birth",
      ]),
    ),
    gioiTinh: readString(data, ["gioi_tinh", "gioiTinh", "gender"]),
    quocTich: readString(
      data,
      ["quoc_tich", "quocTich", "nationality"],
      "Viet Nam",
    ),
    queQuan: readString(data, [
      "que_quan",
      "queQuan",
      "origin_place",
      "home_town",
    ]),
    noiThuongTru: readString(data, [
      "noi_thuong_tru",
      "noiThuongTru",
      "address",
    ]),
    ngayCap: toDisplayDate(
      readString(data, ["ngay_cap", "ngayCap", "issue_date"]),
    ),
    coGiaTriDen: toDisplayDate(
      readString(data, ["co_gia_tri_den", "coGiaTriDen", "expiry_date"]),
    ),
  };
}

function getErrorMessage(status: number): string {
  return ERROR_MESSAGES[status] ?? UNKNOWN_ERROR_MESSAGE;
}

export async function scanCccd(file: File): Promise<CccdResult> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  try {
    const formData = new FormData();

    // 🔥 FIX QUAN TRỌNG NHẤT
    formData.append("file", file); // ✅ phải là "file" (match backend)

    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    console.log("Calling:", API_ENDPOINT);
    console.log("Status:", response.status);

    if (!response.ok) {
      const text = await response.text(); // debug backend trả gì
      console.error("Response text:", text);

      throw new ApiClientError(
        getErrorMessage(response.status),
        response.status,
      );
    }

    // 🔥 tránh lỗi parse khi backend trả HTML (Swagger)
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      throw new ApiClientError(
        "Backend tra ve du lieu khong phai JSON (co the goi sai endpoint).",
      );
    }

    const payload = (await response.json()) as Record<string, unknown>;
    const data = (payload.data as Record<string, unknown>) ?? payload;

    return mapResponseToCccd(data);
  } catch (error) {
    console.error("Scan CCCD error:", error);

    if (error instanceof ApiClientError) throw error;

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError(TIMEOUT_MESSAGE);
    }

    throw new ApiClientError(UNKNOWN_ERROR_MESSAGE);
  } finally {
    clearTimeout(timeoutId);
  }
}
