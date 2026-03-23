from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from . import emoji_norm, formatters, noise_cleaner, quality_filter, unicode_norm, vocab_norm


def clean_text_series(series: pd.Series) -> pd.Series:
    """Quy trình làm sạch một cột văn bản: Unicode -> Nhiễu -> Emoji -> Từ vựng -> Định dạng."""
    cleaned = unicode_norm.normalize_series(series) # Chuẩn hóa Unicode (dựng sẵn, tổ hợp)
    cleaned = noise_cleaner.normalize_series(cleaned) # Làm sạch HTML, URL, Email, SĐT
    cleaned = emoji_norm.normalize_series(cleaned) # Chuyển đổi emoji sang tiếng Việt
    cleaned = vocab_norm.normalize_series(cleaned) # Chuẩn hóa từ vựng/viết tắt
    cleaned = formatters.normalize_series(cleaned) # Chuẩn hóa dấu câu và khoảng trắng
    return cleaned


def preprocess_dataframe(
    frame: pd.DataFrame,
    text_column: str = "content",
    output_column: str | None = None,
    keep_raw: bool = True,
    min_chars: int = quality_filter.SHORT_TEXT_MIN_CHARS,
    drop_duplicates: bool = True,
    keep_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Xử lý tiền xử lý cho toàn bộ DataFrame (tập hợp dữ liệu bảng)."""
    target = frame.copy()
    source_column = text_column
    output_column = output_column or text_column

    # Nếu yêu cầu giữ lại bản gốc, tạo cột mới '{source}_raw' để lưu trữ
    if keep_raw:
        raw_column = f"{source_column}_raw"
        if raw_column not in target.columns:
            target[raw_column] = target[source_column]

    # Thực hiện quy trình làm sạch cho cột văn bản được chọn
    target[output_column] = clean_text_series(target[source_column])

    # Nếu tên cột xuất ra khác tên cột đầu vào, có thể xóa cột đầu vào cũ
    if output_column != source_column:
        target.drop(columns=[source_column], inplace=True, errors="ignore")

    # Lọc bỏ các dòng dữ liệu 'nhiễu' (quá ngắn hoặc bị trùng lặp)
    target = quality_filter.drop_noise_rows(
        target,
        text_column=output_column,
        min_chars=min_chars,
        drop_duplicates=drop_duplicates,
    )

    # Nếu có danh sách các cột cụ thể muốn giữ lại, thực hiện lọc và sắp xếp
    if keep_columns is not None:
        ordered_columns = []
        for column in keep_columns:
            if column in target.columns and column not in ordered_columns:
                ordered_columns.append(column)
        target = target.loc[:, ordered_columns]

    return target


def preprocess_file(
    input_path: str | Path,
    output_path: str | Path | None = None,
    text_column: str = "content",
    keep_raw: bool = True,
    min_chars: int = quality_filter.SHORT_TEXT_MIN_CHARS,
    drop_duplicates: bool = True,
    keep_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Đọc dữ liệu từ file (CSV hoặc JSON), tiến hành tiền xử lý và lưu kết quả ra file mới."""
    path = Path(input_path)
    # Tự động nhận diện định dạng file dựa trên đuôi mở rộng
    frame = pd.read_json(path) if path.suffix.lower() == ".json" else pd.read_csv(path)
    
    # Thực hiện quy trình xử lý trên DataFrame vừa đọc
    cleaned = preprocess_dataframe(
        frame,
        text_column=text_column,
        keep_raw=keep_raw,
        min_chars=min_chars,
        drop_duplicates=drop_duplicates,
        keep_columns=keep_columns,
    )

    # Nếu có chỉ định đường dẫn lưu file
    if output_path is not None:
        output = Path(output_path)
        # Tạo thư mục chứa file nếu chưa tồn tại
        output.parent.mkdir(parents=True, exist_ok=True)
        # Lưu dữ liệu theo định dạng tương ứng
        if output.suffix.lower() == ".json":
            cleaned.to_json(output, orient="records", force_ascii=False, indent=2)
        else:
            cleaned.to_csv(output, index=False)

    return cleaned
