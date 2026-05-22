export type ScannerUiState =
  | "idle"
  | "file_selected"
  | "validation_error"
  | "ready"
  | "loading"
  | "success"
  | "error";

export interface CccdResult {
  soCccd: string;
  hoVaTen: string;
  ngaySinh: string;
  gioiTinh: string;
  quocTich: string;
  queQuan: string;
  noiThuongTru: string;
  ngayCap: string;
  coGiaTriDen: string;
}

export interface FileMeta {
  name: string;
  size: number;
  type: string;
  extension: string;
}

export interface ValidationSuccess {
  valid: true;
  file: File;
  meta: FileMeta;
  compressed: boolean;
}
