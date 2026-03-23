from __future__ import annotations

import re
from typing import Any

import pandas as pd

# Biểu thức chính quy cho các loại khoảng trắng
SPACE_RE = re.compile(r"\s+")
# Biểu thức chính quy để tìm các dấu câu bị lặp lại quá nhiều (từ 3 lần trở lên như !!!, ???)
PUNCT_RE = re.compile(r"([!?.,])\1{2,}")
# Biểu thức chính quy để tìm các ký tự ẩn, ký tự có độ rộng bằng 0 (Zero-width characters)
ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def _to_text(value: Any) -> str | None:
    """Chuyển đổi giá trị đầu vào thành chuỗi, xử lý các giá trị rỗng (None hoặc NaN)."""
    if value is None or pd.isna(value):
        return None
    return str(value)


def normalize_format(value: Any) -> str | None:
    """Chuẩn hóa định dạng văn bản: xử lý dấu câu lặp, xóa ký tự ẩn và làm sạch khoảng trắng."""
    text = _to_text(value)
    if text is None:
        return None
    # Giới hạn các dấu câu lặp lại tối đa 2 lần (ví dụ: !!! -> !!)
    text = PUNCT_RE.sub(r"\1\1", text)
    # Loại bỏ các ký tự ẩn không nhìn thấy được
    text = ZERO_WIDTH_RE.sub("", text)
    # Thay thế tất cả các loại khoảng trắng thừa bằng một dấu cách duy nhất
    text = SPACE_RE.sub(" ", text)
    # Cắt bỏ khoảng trắng ở đầu và cuối văn bản
    return text.strip()


def normalize_series(series: pd.Series) -> pd.Series:
    """Áp dụng hàm chuẩn hóa định dạng cho toàn bộ một cột dữ liệu (Pandas Series)."""
    return series.map(normalize_format)
