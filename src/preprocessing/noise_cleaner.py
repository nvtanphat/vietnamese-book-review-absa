from __future__ import annotations

import re
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup

# Biểu thức chính quy để nhận diện URL (http, https, www)
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
# Biểu thức chính quy để nhận diện Email
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
# Biểu thức chính quy để nhận diện số điện thoại (hỗ trợ nhiều định dạng)
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\d[\s.-]?){8,12}\b")
# Biểu thức chính quy để kiểm nhanh xem văn bản có chứa thẻ HTML hay không
HTML_HINT_RE = re.compile(r"<[^>]+>")


def _to_text(value: Any) -> str | None:
    """Chuyển đổi giá trị đầu vào thành chuỗi, xử lý các giá trị rỗng (None hoặc NaN)."""
    if value is None or pd.isna(value):
        return None
    return str(value)


def strip_html(value: Any) -> str | None:
    """Loại bỏ các thẻ HTML để lấy văn bản thuần túy."""
    text = _to_text(value)
    if text is None:
        return None
    # Nếu không có thẻ HTML (<...>), trả về văn bản gốc để tối ưu hiệu suất
    if not HTML_HINT_RE.search(text):
        return text
    # Sử dụng BeautifulSoup để trích xuất text từ HTML
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)


def normalize_noise(value: Any, url_token: str = "__url__", email_token: str = "__email__", phone_token: str = "__phone__") -> str | None:
    """Làm sạch nhiễu: xóa HTML và thay thế URL, Email, SĐT bằng các từ khóa tượng trưng (token)."""
    text = strip_html(value)
    if text is None:
        return None
    # Thay thế URL bằng token chuyên dụng
    text = URL_RE.sub(url_token, text)
    # Thay thế Email bằng token chuyên dụng
    text = EMAIL_RE.sub(email_token, text)
    # Thay thế Số điện thoại bằng token chuyên dụng
    text = PHONE_RE.sub(phone_token, text)
    return text


def normalize_series(series: pd.Series) -> pd.Series:
    """Áp dụng quy trình làm sạch nhiễu cho toàn bộ một cột dữ liệu (Pandas Series)."""
    return series.map(normalize_noise)
