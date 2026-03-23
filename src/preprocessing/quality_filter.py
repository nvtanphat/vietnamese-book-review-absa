from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

# Hằng số cấu hình cho các bộ lọc chất lượng văn bản
SHORT_TEXT_MIN_CHARS = 10 # Độ dài tối thiểu để xem văn bản là 'có ý nghĩa'
BLANK_MARKERS = {"", "null", "none", "nan"} # Các dấu hiệu dữ liệu trống/lỗi
NAME_ERROR_MARKERS = {"#name?"} # Lỗi định dạng thường gặp trong Excel/CSV
WHITESPACE_RE = re.compile(r"\s+") # Regex cho khoảng trắng


def _to_text(value: Any) -> str:
    """Ép kiểu đầu vào thành chuỗi, trả về chuỗi rỗng nếu giá trị là kiểu rỗng (None/NaN)."""
    if value is None or pd.isna(value):
        return ""
    return str(value)


def normalize_for_duplicate(text: Any) -> str:
    """Chuẩn hóa văn bản dùng cho việc so sánh trùng lặp nội dung."""
    # unicodedata.normalize("NFKC", ...): Đưa các ký tự tổ hợp về dạng tương đương (vd: 'ệ' -> 'ệ')
    # casefold(): Chuẩn hóa chữ hoa chữ thường triệt để hơn lower()
    value = unicodedata.normalize("NFKC", _to_text(text)).casefold()
    # Thay thế các kiểu khoảng trắng phức tạp bằng 1 dấu cách duy nhất
    return WHITESPACE_RE.sub(" ", value).strip()


def is_symbol_only(text: Any) -> bool:
    """Kiểm tra nếu văn bản hoàn toàn là các biểu tượng hoặc ký tự đặc biệt (không phải chữ-số)."""
    value = normalize_for_duplicate(text)
    if not value:
        return False
    # exists alnum: có tồn tại chữ cái hoặc chữ số hay không
    return all(not char.isalnum() for char in value)


def is_digit_only(text: Any) -> bool:
    """Kiểm tra văn bản nếu chỉ chứa chữ số thuần túy."""
    value = normalize_for_duplicate(text)
    return value.isdigit() if value else False


def is_meaningful_text(text: Any, min_chars: int = SHORT_TEXT_MIN_CHARS) -> bool:
    """Hàm trung tâm: Đánh giá một dòng văn bản có đáng để giữ lại hay không."""
    value = normalize_for_duplicate(text)
    if not value: # Rỗng
        return False
    # Kiểm tra các giá trị vô nghĩa
    if value in BLANK_MARKERS or value in NAME_ERROR_MARKERS:
        return False
    # Loại bỏ nếu văn bản chỉ có toàn chữ số hoặc toàn biểu tượng
    if is_digit_only(value) or is_symbol_only(value):
        return False
    # Kiểm tra theo ngưỡng độ dài tối thiểu
    return len(value) >= min_chars


def drop_noise_rows(
    frame: pd.DataFrame,
    text_column: str = "content",
    min_chars: int = SHORT_TEXT_MIN_CHARS,
    drop_duplicates: bool = True,
) -> pd.DataFrame:
    """Hàm lọc DataFrame: Bỏ các dòng ngắn, trùng lặp hoặc vô nghĩa."""
    target = frame.copy()
    text_series = target[text_column]
    
    # Bước 1: Lọc bỏ dựa trên tính 'có ý nghĩa' (meaningful) của văn bản
    keep_mask = text_series.map(lambda value: is_meaningful_text(value, min_chars=min_chars))
    target = target.loc[keep_mask].copy()

    # Bước 2: Lọc bỏ dòng trùng lặp nếu được yêu cầu
    if drop_duplicates and not target.empty:
        # Chuẩn hóa để so sánh nội dung (không thay dữ liệu gốc trong DataFrame)
        normalized = target[text_column].map(normalize_for_duplicate)
        # Loại trùng: chỉ giữ lại dòng xuất hiện đầu tiên (first)
        target = target.loc[~normalized.duplicated(keep="first")].copy()

    # Reset index để mảng thứ tự các dòng được liên tục sau khi xóa
    target.reset_index(drop=True, inplace=True)
    return target
