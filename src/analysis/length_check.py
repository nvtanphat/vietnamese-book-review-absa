from __future__ import annotations

from typing import Any, Mapping, Sequence

from .helpers import numeric_summary, percentage, to_dataframe
from .scan_constants import MIN_TEXT_LENGTH


def scan(records: Sequence[Mapping[str, Any]], text_column: str | None = None) -> dict[str, Any]:
    """Phân tích và thống kê độ dài (số ký tự và số lượng từ) của văn bản trong tập dữ liệu."""
    # Xử lý trường hợp không có dữ liệu hoặc không xác định được cột văn bản
    if not records or not text_column:
        return {
            "text_column": text_column,
            "length_summary": numeric_summary([]),
            "word_summary": numeric_summary([]),
            "length_buckets": {},
            "shorter_than_min_length": 0,
        }

    # Chuyển đổi dữ liệu sang DataFrame để xử lý hiệu quả với Pandas
    df = to_dataframe(records)
    # Lấy cột văn bản, đảm bảo kiểu chuỗi và thay thế giá trị rỗng bằng chuỗi trống
    series = df[text_column].astype("string").fillna("")
    # Tính toán danh sách độ dài ký tự của mỗi dòng
    lengths = series.str.len().astype(int).tolist()
    # Tính toán danh sách số lượng từ (tách theo khoảng trắng) của mỗi dòng
    words = series.str.split().map(len).tolist()

    # Đếm số lượng các dòng có độ dài nhỏ hơn ngưỡng tối thiểu quy định
    shorter_than_min_length = sum(length < MIN_TEXT_LENGTH for length in lengths)
    
    # Chia nhóm (buckets) độ dài để phân tích sự phân bổ của dữ liệu
    buckets = {
        f"<{MIN_TEXT_LENGTH}": 0, # Nhóm cực ngắn (thường là rác)
        f"{MIN_TEXT_LENGTH}-{MIN_TEXT_LENGTH * 2 - 1}": 0,
        f"{MIN_TEXT_LENGTH * 2}-{MIN_TEXT_LENGTH * 5 - 1}": 0,
        f"{MIN_TEXT_LENGTH * 5}-{MIN_TEXT_LENGTH * 10 - 1}": 0,
        f">={MIN_TEXT_LENGTH * 10}": 0, # Nhóm văn bản dài
    }

    # Phân loại độ dài của từng dòng vào các nhóm tương ứng
    for length in lengths:
        if length < MIN_TEXT_LENGTH:
            buckets[f"<{MIN_TEXT_LENGTH}"] += 1
        elif length < MIN_TEXT_LENGTH * 2:
            buckets[f"{MIN_TEXT_LENGTH}-{MIN_TEXT_LENGTH * 2 - 1}"] += 1
        elif length < MIN_TEXT_LENGTH * 5:
            buckets[f"{MIN_TEXT_LENGTH * 2}-{MIN_TEXT_LENGTH * 5 - 1}"] += 1
        elif length < MIN_TEXT_LENGTH * 10:
            buckets[f"{MIN_TEXT_LENGTH * 5}-{MIN_TEXT_LENGTH * 10 - 1}"] += 1
        else:
            buckets[f">={MIN_TEXT_LENGTH * 10}"] += 1

    # Trả về kết quả phân tích thống kê chi tiết
    return {
        "text_column": text_column,
        "length_summary": numeric_summary(lengths), # Thống kê số học về ký tự (TB, trung vị, SD...)
        "word_summary": numeric_summary(words), # Thống kê số học về số lượng từ
        "length_buckets": buckets, # Dữ liệu phân bổ theo các nhóm độ dài
        "shorter_than_min_length": shorter_than_min_length, # Số dòng bị ngắn hơn ngưỡng tối thiểu
        "shorter_than_min_length_ratio": percentage(shorter_than_min_length, len(records)), # Tỉ lệ % dòng ngắn
    }
