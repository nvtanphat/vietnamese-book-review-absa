from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from .helpers import normalize_for_duplicate, percentage, to_dataframe


def scan(records: Sequence[Mapping[str, Any]], text_column: str | None = None) -> dict[str, Any]:
    """Thống kê các bản ghi và đoạn văn bản bị trùng lặp trong bộ dữ liệu."""
    # Xử lý trường hợp danh sách dữ liệu rỗng
    if not records:
        return {
            "exact_duplicate_rows": 0,
            "normalized_duplicate_texts": 0,
            "exact_duplicate_rows_ratio": 0.0,
            "normalized_duplicate_texts_ratio": 0.0,
            "top_duplicate_texts": [],
        }

    # Chuyển đổi dữ liệu sang DataFrame để sử dụng các hàm tối ưu của Pandas
    df = to_dataframe(records)
    # 1. Đếm số lượng dòng trùng lặp tuyệt đối (giống nhau ở tất cả các cột)
    exact_duplicate_rows = int(df.duplicated().sum())

    text_counter = Counter()
    normalized_text_counter = Counter()
    
    # Nếu xác định được cột chứa văn bản chính, tiến hành phân tích trùng lặp nội dung
    if text_column and text_column in df.columns:
        text_series = df[text_column].fillna("").astype(str)
        # Đếm tần suất xuất hiện của văn bản nguyên bản
        text_counter.update(text_series.tolist())
        # Đếm tần suất sau khi chuẩn hóa nội dung (để phát hiện trùng lặp về ngữ nghĩa/ký tự ẩn)
        normalized_text_counter.update(text_series.map(normalize_for_duplicate).tolist())

    # 2. Tính tổng số lượng văn bản bị lặp (số bản copy vượt mức 1 của mỗi nội dung duy nhất)
    normalized_duplicate_texts = sum(count - 1 for count in normalized_text_counter.values() if count > 1)

    # 3. Tìm ra top 10 đoạn văn bản bị lặp lại nhiều nhất để cảnh báo
    top_duplicate_texts = [
        {"text": text, "count": count}
        for text, count in text_counter.most_common(10)
        if count > 1
    ]

    # Trả về kết quả phân tích dưới dạng từ điển (dictionary)
    return {
        "exact_duplicate_rows": exact_duplicate_rows, # Số dòng trùng lặp hoàn toàn
        "normalized_duplicate_texts": normalized_duplicate_texts, # Số văn bản trùng sau chuẩn hóa
        "exact_duplicate_rows_ratio": percentage(exact_duplicate_rows, len(records)), # Tỉ lệ % dòng trùng
        "normalized_duplicate_texts_ratio": percentage(normalized_duplicate_texts, len(records)), # Tỉ lệ % văn bản trùng
        "top_duplicate_texts": top_duplicate_texts, # Danh sách văn bản trùng nhiều nhất
    }
