from __future__ import annotations

from collections import Counter
import warnings
from typing import Any, Mapping, Sequence

from .helpers import (
    EMAIL_RE,
    ELONGATED_RE,
    MD_LINK_RE,
    PHONE_RE,
    PUNCT_REPEAT_RE,
    URL_RE,
    is_digit_only,
    is_symbol_only,
    percentage,
    to_text,
)

# Thử nghiệm import thư viện BeautifulSoup để nhận diện chính xác các cấu trúc thẻ HTML
try:
    from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
except Exception:  # pragma: no cover - fallback nếu môi trường chưa cài đặt thư viện
    BeautifulSoup = None
    MarkupResemblesLocatorWarning = None


def scan(records: Sequence[Mapping[str, Any]], text_column: str | None = None) -> dict[str, Any]:
    """Phát hiện và thống kê các loại nhiễu (noise) phổ biến trong tập dữ liệu văn bản."""
    # Xử lý trường hợp dữ liệu rỗng hoặc không xác định được cột văn bản cần quét
    if not records or not text_column:
        return {
            "text_column": text_column,
            "pattern_counts": {},
            "rows_with_any_noise": 0,
            "rows_with_any_noise_ratio": 0.0,
            "examples": {},
        }

    pattern_counts = Counter() # Đếm số lượng cụ thể của từng loại nhiễu phát hiện được
    # Lưu trữ một vài ví dụ minh họa cho mỗi loại nhiễu để người dùng dễ kiểm chứng
    examples: dict[str, list[str]] = {
        "url": [],
        "email": [],
        "phone": [],
        "html": [],
        "markdown_link": [],
        "punct_repeat": [],
        "elongated": [],
        "digit_only": [],
        "symbol_only": [],
    }
    rows_with_any_noise = 0 # Đếm tổng số lượng dòng (records) gặp ít nhất một loại nhiễu

    for row in records:
        text = to_text(row.get(text_column))
        row_has_noise = False

        # 1. Phát hiện đường dẫn liên kết (URL)
        if URL_RE.search(text):
            pattern_counts["url"] += 1
            row_has_noise = True
            if len(examples["url"]) < 3:
                examples["url"].append(text)
        
        # 2. Phát hiện địa chỉ thư điện tử (Email)
        if EMAIL_RE.search(text):
            pattern_counts["email"] += 1
            row_has_noise = True
            if len(examples["email"]) < 3:
                examples["email"].append(text)
        
        # 3. Phát hiện định dạng số điện thoại
        if PHONE_RE.search(text):
            pattern_counts["phone"] += 1
            row_has_noise = True
            if len(examples["phone"]) < 3:
                examples["phone"].append(text)
        
        # 4. Phát hiện các thẻ hoặc mã HTML (ưu tiên dùng BeautifulSoup nếu có)
        if BeautifulSoup is not None and "<" in text and ">" in text:
            with warnings.catch_warnings():
                if MarkupResemblesLocatorWarning is not None:
                    warnings.simplefilter("ignore", MarkupResemblesLocatorWarning)
                soup = BeautifulSoup(text, "html.parser")
            if soup.find():
                pattern_counts["html"] += 1
                row_has_noise = True
                if len(examples["html"]) < 3:
                    examples["html"].append(text)
                if row_has_noise:
                    rows_with_any_noise += 1
                continue
        elif "<" in text and ">" in text: # Phương án nhận diện thô nếu không dùng bs4
            pattern_counts["html"] += 1
            row_has_noise = True
            if len(examples["html"]) < 3:
                examples["html"].append(text)

        # 5. Phát hiện định dạng liên kết Markdown [text](url)
        if MD_LINK_RE.search(text):
            pattern_counts["markdown_link"] += 1
            row_has_noise = True
            if len(examples["markdown_link"]) < 3:
                examples["markdown_link"].append(text)

        # 6. Phát hiện các dấu câu lặp lại liên tiếp (vd: !!!, ???)
        if PUNCT_REPEAT_RE.search(text):
            pattern_counts["punct_repeat"] += 1
            row_has_noise = True
            if len(examples["punct_repeat"]) < 3:
                examples["punct_repeat"].append(text)

        # 7. Phát hiện các từ bị kéo dài ký tự một cách bất thường (vd: rấtttt, quáaaa)
        if ELONGATED_RE.search(text):
            pattern_counts["elongated"] += 1
            row_has_noise = True
            if len(examples["elongated"]) < 3:
                examples["elongated"].append(text)

        # 8. Phát hiện các dòng văn bản chỉ chứa chữ số thuần túy
        if is_digit_only(text):
            pattern_counts["digit_only"] += 1
            row_has_noise = True
            if len(examples["digit_only"]) < 3:
                examples["digit_only"].append(text)

        # 9. Phát hiện các dòng văn bản chỉ chứa ký hiệu đặc biệt
        if is_symbol_only(text):
            pattern_counts["symbol_only"] += 1
            row_has_noise = True
            if len(examples["symbol_only"]) < 3:
                examples["symbol_only"].append(text)

        # Nếu dòng dữ liệu này gặp bất kỳ vấn đề nhiễu nào ở trên
        if row_has_noise:
            rows_with_any_noise += 1

    # Trả về kết quả phân tích thống kê nhiễu dưới dạng cấu trúc báo cáo (report)
    return {
        "text_column": text_column,
        "pattern_counts": dict(pattern_counts), # Chi tiết số lượng của từng loại nhiễu
        "rows_with_any_noise": rows_with_any_noise, # Tổng số dòng bị nhiễu
        "rows_with_any_noise_ratio": percentage(rows_with_any_noise, len(records)), # Tỉ lệ % dòng nhiễu
        "examples": examples, # Danh sách các ví dụ minh họa
    }
