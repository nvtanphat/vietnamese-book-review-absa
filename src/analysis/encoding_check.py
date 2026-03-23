from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

# Import các hằng số và regex hỗ trợ kiểm tra lỗi mã hóa văn bản từ module helpers
from .helpers import CONTROL_RE, MOJIBAKE_HINT_RE, REPLACEMENT_CHAR, ZERO_WIDTH_RE, percentage, to_text

# Thử nghiệm import thư viện ftfy để kiểm tra khả năng tự động sửa lỗi mã hóa
try:
    from ftfy import fix_text
except Exception:  # pragma: no cover - fallback nếu môi trường chưa cài đặt thư viện
    fix_text = None


def scan(records: Sequence[Mapping[str, Any]], text_column: str | None = None) -> dict[str, Any]:
    """Phân tích các vấn đề liên quan đến mã hóa (Unicode, ký tự ẩn, Mojibake) trong tập dữ liệu."""
    # Xử lý trường hợp dữ liệu rỗng hoặc không xác định được cột văn bản cần quét
    if not records or not text_column:
        return {
            "text_column": text_column,
            "issue_counts": {},
            "rows_with_any_issue": 0,
            "rows_with_any_issue_ratio": 0.0,
            "examples": {},
        }

    issue_counts = Counter() # Đếm số lượng từng loại lỗi mã hóa phát hiện được
    # Lưu trữ một vài ví dụ minh họa cho từng loại lỗi để người dùng dễ kiểm chứng
    examples: dict[str, list[str]] = {
        "replacement_char": [], # Lỗi ký tự thay thế () - thường do giải mã sai
        "zero_width": [], # Ký tự có độ rộng bằng 0 (ký tự ẩn)
        "control_char": [], # Ký tự điều khiển rác (non-printable)
        "mojibake_hint": [], # Các dấu hiệu của lỗi hiển thị phông chữ (mojibake)
    }
    rows_with_any_issue = 0 # Đếm tổng số lượng dòng gặp ít nhất một trong các vấn đề trên

    for row in records:
        text = to_text(row.get(text_column))
        row_has_issue = False

        # 1. Phát hiện ký tự thay thế ( - U+FFFD)
        if REPLACEMENT_CHAR in text:
            issue_counts["replacement_char"] += 1
            row_has_issue = True
            if len(examples["replacement_char"]) < 3:
                examples["replacement_char"].append(text)

        # 2. Phát hiện ký tự ẩn (zero-width characters)
        if ZERO_WIDTH_RE.search(text):
            issue_counts["zero_width"] += 1
            row_has_issue = True
            if len(examples["zero_width"]) < 3:
                examples["zero_width"].append(text)

        # 3. Phát hiện ký tự điều khiển (control characters) rác trong văn bản
        if CONTROL_RE.search(text):
            issue_counts["control_char"] += 1
            row_has_issue = True
            if len(examples["control_char"]) < 3:
                examples["control_char"].append(text)

        # 4. Nhận diện các dấu hiệu của lỗi Mojibake (lỗi font/encoding)
        if MOJIBAKE_HINT_RE.search(text):
            issue_counts["mojibake_hint"] += 1
            row_has_issue = True
            if len(examples["mojibake_hint"]) < 3:
                examples["mojibake_hint"].append(text)

        # 5. Kiểm tra nếu công cụ 'ftfy' có thể sửa được văn bản này (dấu hiệu của lỗi mã hóa fix được)
        if fix_text is not None and fix_text(text) != text:
            issue_counts["fixable_encoding"] += 1
            row_has_issue = True
            if "fixable_encoding" not in examples:
                examples["fixable_encoding"] = []
            if len(examples["fixable_encoding"]) < 3:
                examples["fixable_encoding"].append(text)

        # Nếu dòng dữ liệu hiện tại gặp bất kỳ lỗi nào nêu trên
        if row_has_issue:
            rows_with_any_issue += 1

    # Trả về kết quả phân tích tổng hợp dưới dạng cấu trúc báo cáo (report)
    return {
        "text_column": text_column,
        "issue_counts": dict(issue_counts), # Số lượng cụ thể mỗi loại lỗi mã hóa
        "rows_with_any_issue": rows_with_any_issue, # Tổng số dòng có lỗi
        "rows_with_any_issue_ratio": percentage(rows_with_any_issue, len(records)), # Tỉ lệ % dòng lỗi
        "examples": examples, # Các đoạn văn bản mẫu chứa lỗi để tham khảo
    }
