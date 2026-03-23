from __future__ import annotations

import re
from typing import Any

import emoji
import pandas as pd

from .map_utils import load_json_map

# Biểu thức chính quy để tìm các hậu tố màu da (ví dụ: _light_skin_tone)
SKIN_TONE_SUFFIX_RE = re.compile(r"_(?:light|medium_light|medium|medium_dark|dark)_skin_tone$")
# Tải bản đồ emoji từ file JSON để tra cứu tên tiếng Việt
EMOJI_MAP = load_json_map("emoji_map.json")


def _to_text(value: Any) -> str | None:
    """Chuyển đổi giá trị đầu vào thành chuỗi, xử lý các giá trị rỗng (None hoặc NaN)."""
    if value is None or pd.isna(value):
        return None
    return str(value)


def _normalize_alias(alias: str) -> str:
    """Chuẩn hóa tên gọi emoji: chuyển sang chữ thường, thay ký tự đặc biệt bằng '_', xóa '_' ở đầu/cuối."""
    alias = alias.lower()
    alias = re.sub(r"[^a-z0-9]+", "_", alias)
    return alias.strip("_")


def demojize_text(value: Any, separator: str = " ") -> str | None:
    """Hàm chính để chuyển đổi emoji trong văn bản thành tên gọi tiếng Việt."""
    text = _to_text(value)
    if text is None:
        return None

    # Chuyển đổi emoji thực tế thành mã tên tiếng Anh (ví dụ: 😀 -> :grinning_face:)
    text = emoji.demojize(text, language="en")

    def replace_token(match: re.Match[str]) -> str:
        """Xử lý từng mã emoji tìm thấy trong văn bản."""
        key = _normalize_alias(match.group(1))
        # Loại bỏ thông tin về màu da (nếu có) để tìm tên gốc
        base_key = _normalize_alias(SKIN_TONE_SUFFIX_RE.sub("", key))
        # Tra cứu trong EMOJI_MAP: ưu tiên tên đầy đủ -> tên gốc -> mặc định 'emoji_tên_gốc'
        return EMOJI_MAP.get(key, EMOJI_MAP.get(base_key, f"emoji_{base_key}"))

    # Tìm các cụm :tên_emoji: và gọi hàm replace_token để thay thế
    text = re.sub(r":([^:]+):", replace_token, text)
    # Loại bỏ khoảng trắng thừa (nhiều dấu cách thành một) và cắt khoảng trắng 2 đầu
    return re.sub(r"\s+", " ", text).strip()


def normalize_series(series: pd.Series) -> pd.Series:
    """Áp dụng hàm xử lý emoji cho toàn bộ cột dữ liệu của Pandas."""
    return series.map(demojize_text)
