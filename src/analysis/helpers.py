from __future__ import annotations

import re
import statistics
import unicodedata
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

from .scan_constants import LABEL_COLUMN_PRIORITY, TEXT_COLUMN_PRIORITY

# Thử nghiệm import thư viện emoji để hỗ trợ xử lý biểu tượng cảm xúc
try:
    import emoji
except Exception:  # pragma: no cover - fallback nếu không có thư viện
    emoji = None

# --- Định nghĩa các biểu thức chính quy (Regex) để nhận diện định dạng dữ liệu ---
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\b(?:\+?84|0)\d{8,10}\b")
HTML_TAG_RE = re.compile(r"<[^>]+>")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")
ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]") # Ký tự ẩn có độ rộng bằng 0
CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]") # Ký tự điều khiển (non-printable)
MOJIBAKE_HINT_RE = re.compile(r"(Ã.|Â.|Ä.|á».|ðŸ|â€|â€™)") # Dấu hiệu của lỗi phông chữ (mojibake)
PUNCT_REPEAT_RE = re.compile(r"([!?.,])\1{1,}") # Dấu câu lặp lại (vd: !!!)
ELONGATED_RE = re.compile(r"([A-Za-zÀ-ỹ])\1{2,}", re.UNICODE) # Từ bị kéo dài (vd: hayyy)

# Regex phạm vi rộng để nhận diện emoji (dành cho việc quét dữ liệu nhanh)
EMOJI_RE = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF" "\U0001F300-\U0001F5FF" "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF" "\U0001F700-\U0001F77F" "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF" "\U0001F900-\U0001F9FF" "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF" "\u2700-\u27BF"
    "]",
    re.UNICODE,
)

REPLACEMENT_CHAR = "\uFFFD" # Ký tự thường xuất hiện khi lỗi giải mã (decode)


def to_text(value: Any) -> str:
    """Chuyển đổi giá trị bất kỳ sang kiểu chuỗi (string) một cách an toàn."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def is_blank(value: Any) -> bool:
    """Kiểm tra xem một giá trị có phải là rỗng, null hoặc các biến thể của NaN hay không."""
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        # Loại bỏ các chuỗi văn bản thường đại diện cho giá trị rỗng
        return stripped == "" or stripped.lower() in {"null", "none", "nan"}
    return False


def normalize_text(text: Any) -> str:
    """Chuẩn hóa Unicode về dạng NFKC và loại bỏ khoảng trắng ở hai đầu."""
    value = unicodedata.normalize("NFKC", to_text(text))
    return value.strip()


def normalize_for_duplicate(text: Any) -> str:
    """Chuẩn hóa văn bản dành cho việc so sánh trùng lặp: viết thường và thu gọn khoảng trắng."""
    value = normalize_text(text).casefold()
    value = re.sub(r"\s+", " ", value)
    return value


def collapse_whitespace(text: str) -> str:
    """Thay thế các chuỗi khoảng trắng phức tạp bằng một dấu cách duy nhất."""
    return re.sub(r"\s+", " ", text).strip()


def safe_float(value: Any) -> float | None:
    """Chuyển đổi một giá trị sang số thực (float) an toàn, trả về None nếu thất bại."""
    if is_blank(value):
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def numeric_summary(values: Sequence[float]) -> dict[str, Any]:
    """Tính toán các chỉ số thống kê mô tả (min, max, mean, median, stdev, percentiles)."""
    if not values:
        return {
            "count": 0, "min": None, "max": None, "mean": None,
            "median": None, "stdev": None, "p25": None, "p75": None,
        }

    ordered = sorted(values)
    count = len(ordered)
    mean = statistics.fmean(ordered)
    median = statistics.median(ordered)
    # Tính độ lệch chuẩn quần thể
    stdev = statistics.pstdev(ordered) if count > 1 else 0.0
    # Lấy giá trị tại các phân vị 25% và 75%
    p25 = ordered[min(count - 1, max(0, round(0.25 * (count - 1))))]
    p75 = ordered[min(count - 1, max(0, round(0.75 * (count - 1))))]
    return {
        "count": count, "min": ordered[0], "max": ordered[-1],
        "mean": mean, "median": median, "stdev": stdev,
        "p25": p25, "p75": p75,
    }


def percentage(part: int, whole: int) -> float:
    """Tính phần trăm của một phần so với tổng số, làm tròn 2 chữ số thập phân."""
    if whole <= 0:
        return 0.0
    return round(part * 100.0 / whole, 2)


def detect_text_column(records: Sequence[Mapping[str, Any]]) -> str | None:
    """Tự động nhận diện cột chứa văn bản chính dựa trên độ ưu tiên tên cột hoặc nội dung thực tế."""
    if not records:
        return None
    columns = list(records[0].keys())
    # 1. Thử tìm dựa trên tên các cột ưu tiên (ví dụ: 'content', 'text'...)
    for preferred in TEXT_COLUMN_PRIORITY:
        if preferred in columns:
            return preferred

    # 2. Nếu không thấy, chọn cột có số lượng dữ liệu thực tế nhiều nhất (quét 100 bản ghi đầu)
    best_column = None
    best_score = -1
    for column in columns:
        score = 0
        for row in records[:100]:
            if not is_blank(row.get(column)):
                score += 1
        if score > best_score:
            best_score = score
            best_column = column
    return best_column


def detect_label_columns(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Tự động phát hiện các cột chứa nhãn (labels) dựa trên danh sách tên ưu tiên."""
    if not records:
        return []
    columns = list(records[0].keys())
    # Lọc các cột có tên thường dùng làm nhãn (rating, sentiment...)
    ordered = [column for column in LABEL_COLUMN_PRIORITY if column in columns]
    if ordered:
        return ordered
    # Nếu không có, mặc định lấy tất cả các cột trừ cột văn bản đã nhận diện
    text_column = detect_text_column(records)
    return [column for column in columns if column != text_column]


def count_emojis(text: str) -> list[str]:
    """Trích xuất tất cả các biểu tượng cảm xúc (emoji) trong đoạn văn bản thành một danh sách."""
    if emoji is not None:
        try:
            return [item["emoji"] for item in emoji.emoji_list(text)]
        except Exception:
            pass
    return EMOJI_RE.findall(text)


def emoji_name(value: str) -> str:
    """Lấy tên tiếng Anh mô tả emoji (ví dụ: 😀 -> grinning_face)."""
    if emoji is not None:
        try:
            return emoji.demojize(value, language="en").strip(":")
        except Exception:
            return value
    return value


def is_symbol_only(text: str) -> bool:
    """Kiểm tra văn bản có phải chỉ chứa toàn các ký hiệu đặc biệt mà không có chữ/số."""
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return False
    return all(not ch.isalnum() for ch in stripped)


def is_digit_only(text: str) -> bool:
    """Kiểm tra văn bản có phải chỉ chứa toàn các chữ số thuần túy."""
    stripped = re.sub(r"\s+", "", text)
    return stripped.isdigit() if stripped else False


def top_items(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    """Lấy danh sách các phần tử xuất hiện nhiều nhất từ một bộ đếm Counter."""
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def to_dataframe(records: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    """Chuyển đổi danh sách bản ghi (list of dicts) sang Pandas DataFrame."""
    return pd.DataFrame.from_records(records)
