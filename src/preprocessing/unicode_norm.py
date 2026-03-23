from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import regex as re

# Thử import thư viện ftfy để tự động sửa các lỗi mã hóa văn bản (mojibake) thường gặp
try:
    from ftfy import fix_text
except ImportError:  # Nếu không cài ftfy, hàm fix_text sẽ trả về nguyên bản văn bản
    def fix_text(text: str) -> str:
        return text

# Biểu thức chính quy sử dụng thư viện regex để tìm ký tự điều khiển (Cc) và ký tự định dạng (Cf)
_CTRL_OR_FORMAT = re.compile(r"[\p{Cc}\p{Cf}]")
# Các ký tự đặc biệt cần giữ lại dù thuộc nhóm điều khiển/định dạng (xuống dòng, tab,...)
_KEEP = {"\n", "\r", "\t", "\u200c", "\u200d"}


def normalize_unicode(value: Any) -> str | None:
    """Quy trình chuẩn hóa Unicode: Sửa lỗi hiển thị -> NFC -> Lọc bỏ ký tự ẩn/rác."""
    if value is None or pd.isna(value):
        return None

    # Bước 1: Sửa các lỗi văn bản bị lỗi font hoặc lỗi mã hóa (mojibake)
    text = fix_text(str(value))
    # Bước 2: Chuẩn hóa về dạng NFC (Dạng kết hợp các ký tự dấu vào chữ cái gốc)
    text = unicodedata.normalize("NFC", text)

    cleaned: list[str] = []
    # Bước 3: Duyệt từng ký tự để loại bỏ các ký tự rác không mong muốn
    for char in text:
        # Nếu là ký tự nằm trong danh sách cần giữ lại
        if char in _KEEP:
            cleaned.append(char)
            continue
        # Nếu là ký tự điều khiển hoặc ký tự định dạng ẩn, thực hiện bỏ qua
        if _CTRL_OR_FORMAT.fullmatch(char):
            continue
        # Các ký tự bình thường khác được giữ lại
        cleaned.append(char)

    # Nối lại thành chuỗi hoàn chỉnh và đảm bảo chuẩn hóa NFC một lần nữa
    return unicodedata.normalize("NFC", "".join(cleaned))


# Các bí danh (aliases) của hàm chuẩn hóa để phục vụ các mục đích gọi tên khác nhau
def normalize_text(value: Any) -> str | None:
    return normalize_unicode(value)


def repair_mojibake(value: Any) -> str | None:
    return normalize_unicode(value)


def normalize_nfc(value: Any) -> str | None:
    return normalize_unicode(value)


def normalize_series(series: pd.Series) -> pd.Series:
    """Áp dụng chuẩn hóa Unicode cho toàn bộ một cột dữ liệu (Pandas Series)."""
    return series.map(normalize_unicode)


def normalize_dataframe(
    frame: pd.DataFrame,
    text_column: str,
    output_column: str | None = None,
    inplace: bool = False,
) -> pd.DataFrame:
    """Thực hiện chuẩn hóa Unicode cho một cột nhất định trong DataFrame bảng dữ liệu."""
    target = frame if inplace else frame.copy()
    column = output_column or text_column
    target[column] = normalize_series(target[text_column])
    return target


def normalize_file(input_path: str | Path, output_path: str | Path | None = None, text_column: str = "content") -> pd.DataFrame:
    """Đọc dữ liệu từ file (CSV/JSON), chuẩn hóa Unicode và lưu kết quả ra file mới."""
    path = Path(input_path)
    # Tự động nhận diện định dạng file đầu vào
    frame = pd.read_json(path) if path.suffix.lower() == ".json" else pd.read_csv(path)
    # Thực hiện chuẩn hóa trên DataFrame vừa đọc
    cleaned = normalize_dataframe(frame, text_column=text_column)

    # Nếu có đường dẫn yêu cầu lưu file
    if output_path is not None:
        output = Path(output_path)
        # Tạo thư mục đích nếu chưa có
        output.parent.mkdir(parents=True, exist_ok=True)
        # Lưu file theo định dạng JSON (records) hoặc CSV
        if output.suffix.lower() == ".json":
            cleaned.to_json(output, orient="records", force_ascii=False, indent=2)
        else:
            cleaned.to_csv(output, index=False)

    return cleaned
