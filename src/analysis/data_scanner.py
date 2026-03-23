from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

# Import các loại kiểm tra khác nhau từ thư mục cùng cấp (.)
from . import (
    duplicate_check,
    emoji_check,
    encoding_check,
    label_distribution_check,
    length_check,
    missing_values_check,
    noise_pattern_check,
    overview_check,
    vocab_check,
)
from .helpers import detect_text_column
from .scan_constants import DEFAULT_INPUT_CANDIDATES

# Danh sách các hạng mục kiểm tra dữ liệu sẽ được thực thi khi chạy scanner
CHECKS = (
    ("overview", overview_check.scan), # Tổng quan: số dòng, số cột
    ("missing_values", missing_values_check.scan), # Phát hiện dữ liệu bị khuyết thiếu
    ("length", length_check.scan), # Phân tích độ dài văn bản (quá ngắn/dài)
    ("encoding", encoding_check.scan), # Tìm lỗi mã hóa văn bản hoặc ký tự rác
    ("noise_patterns", noise_pattern_check.scan), # Phát hiện mẫu nhiễu: HTML, URL, Email...
    ("emoji", emoji_check.scan), # Thống kê biểu tượng cảm xúc (emoji)
    ("vocab", vocab_check.scan), # Phân tích từ vựng: từ lạ, từ viết tắt, tiếng lóng
    ("duplicates", duplicate_check.scan), # Tìm các dòng văn bản bị lặp lại
    ("labels", label_distribution_check.scan), # Phân tích sự cân bằng trong phân bổ nhãn (sentiment)
)


def resolve_input_path(input_path: str | Path | None = None) -> Path:
    """Xác định đường dẫn chính xác của file đầu vào từ các gợi ý hoặc thư mục truyền vào."""
    if input_path is not None:
        path = Path(input_path)
        if path.is_dir():
            # Nếu truyền vào thư mục, tự động tìm kiếm bộ dữ liệu mẫu mặc định bên trong
            for candidate in DEFAULT_INPUT_CANDIDATES:
                candidate_path = path / candidate.name
                if candidate_path.exists():
                    return candidate_path
        return path

    # Nếu không truyền đường dẫn, tìm kiếm trong các thư mục thô (raw) của dự án
    for candidate in DEFAULT_INPUT_CANDIDATES:
        if candidate.exists():
            return candidate
    return DEFAULT_INPUT_CANDIDATES[0]


def _read_text_file(path: Path, encoding: str) -> list[dict[str, Any]]:
    """Đọc dữ liệu từ định dạng JSON hoặc CSV và chuyển đổi thành danh sách các dictionary."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        frame = pd.read_json(path, encoding=encoding)
        return frame.to_dict(orient="records")

    if suffix == ".csv":
        frame = pd.read_csv(path, encoding=encoding)
        return frame.to_dict(orient="records")

    raise ValueError(f"Định dạng tệp không được hỗ trợ: {suffix}")


def load_records(path: str | Path) -> list[dict[str, Any]]:
    """Tải dữ liệu từ file, thử nghiệm nhiều hệ mã hóa (encoding) để tránh lỗi phông chữ tiếng Việt."""
    source = Path(path)
    errors: list[str] = []
    # Thử lần lượt các bảng mã phổ biến: utf-8 (có/không BOM) và windows-1258 cho tiếng Việt
    for encoding in ("utf-8-sig", "utf-8", "cp1258", "cp1252"):
        try:
            return _read_text_file(source, encoding)
        except Exception as exc:  # pragma: no cover
            errors.append(f"{encoding}: {exc}")
    # Nếu tất cả bảng mã đều thất bại
    raise RuntimeError(f"Không thể đọc được file {source}. Đã thử các bảng mã: {'; '.join(errors)}")


class DataScanner:
    """Lớp công cụ chính để thực hiện quét (scan) chất lượng dữ liệu văn bản."""
    def __init__(self, records: Sequence[Mapping[str, Any]], source_path: str | Path | None = None) -> None:
        # Chuẩn hóa dữ liệu đầu vào thành danh sách các dictionary đơn giản
        self.records = [dict(row) for row in records]
        self.source_path = str(source_path) if source_path is not None else None
        # Tự động phát hiện cột chứa văn bản chính dựa trên nội dung dữ liệu
        self.text_column = detect_text_column(self.records)

    @classmethod
    def from_path(cls, path: str | Path | None = None) -> "DataScanner":
        """Phím tắt để khởi tạo trực tiếp Scanner từ một đường dẫn file trên ổ đĩa."""
        resolved = resolve_input_path(path)
        return cls(load_records(resolved), resolved)

    def run(self) -> dict[str, Any]:
        """Quy trình thực thi tất cả các bài kiểm tra đã cấu hình và trả về một báo cáo tổng hợp."""
        report: dict[str, Any] = {
            "metadata": {
                "source_path": self.source_path,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "row_count": len(self.records),
                "column_count": len(self.records[0]) if self.records else 0,
                "text_column": self.text_column,
            },
            "checks": {},
        }

        # Duyệt và chạy từng hàm check tương ứng trong CHECKS
        for name, check_fn in CHECKS:
            report["checks"][name] = check_fn(self.records, self.text_column)

        return report

    def save(self, output_path: str | Path, report: dict[str, Any] | None = None) -> Path:
        """Lưu báo cáo phân tích chất lượng dữ liệu (dưới dạng file JSON)."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        # Nếu báo cáo chưa được chạy, tự động thực thi hàm run()
        payload = report if report is not None else self.run()
        with output.open("w", encoding="utf-8", newline="") as handle:
            # indent=2 giúp văn bản JSON được căn lề thụt đầu dòng dễ đọc
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return output


# Các hàm hỗ trợ chạy nhanh cho các bản ghi hoặc đường dẫn cụ thể
def scan_records(records: Sequence[Mapping[str, Any]], source_path: str | Path | None = None) -> dict[str, Any]:
    return DataScanner(records, source_path).run()


def scan_path(path: str | Path | None = None) -> dict[str, Any]:
    return DataScanner.from_path(path).run()
