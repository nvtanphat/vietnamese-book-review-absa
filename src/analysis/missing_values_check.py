from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd

from .helpers import percentage, to_dataframe


def scan(records: Sequence[Mapping[str, Any]], text_column: str | None = None) -> dict[str, Any]:
    """Phân tích và thống kê các giá trị bị khuyết thiếu (missing/blank) trong toàn bộ dữ liệu."""
    # Chuyển đổi dữ liệu sang dạng DataFrame để xử lý tập trung
    df = to_dataframe(records)
    rows = int(df.shape[0]) # Tổng số lượng dòng dữ liệu
    columns = list(df.columns) # Danh sách tất cả các cột có trong dữ liệu

    per_column: dict[str, dict[str, Any]] = {}
    missing_rows = 0

    # Các từ khóa thường gặp đại diện cho giá trị rỗng trong dữ liệu chưa làm sạch
    blank_like = {"", "null", "none", "nan"}
    # Chuyển đổi dữ liệu sang kiểu chuỗi để đồng bộ việc kiểm tra văn bản
    normalized = df.astype("string")
    
    # Tạo mặt nạ đánh dấu ô trống: 
    # Được coi là trống nếu là giá trị thực sự rỗng (NaN) hoặc là các chuỗi vô nghĩa trong 'blank_like'
    missing_mask = normalized.isna() | normalized.apply(
        lambda series: series.str.strip().str.lower().isin(blank_like)
    )
    # Tổng hợp số lượng ô trống theo từng cột (axis=0)
    missing_series = missing_mask.sum(axis=0)

    for column in columns:
        missing = int(missing_series[column])
        # Lưu báo cáo chi tiết cho từng cột cụ thể
        per_column[column] = {
            "missing_count": missing,
            "missing_ratio": percentage(missing, rows),
        }

    # Đếm số lượng dòng mà có ít nhất một giá trị bị thiếu ở bất kỳ cột nào
    missing_rows = int(missing_mask.any(axis=1).sum())

    # Sắp xếp danh sách các cột theo mức độ bị thiếu dữ liệu (từ nhiều nhất đến ít nhất)
    sorted_columns = sorted(
        per_column.items(),
        key=lambda item: (item[1]["missing_count"], item[0]),
        reverse=True,
    )

    # Trả về kết quả phân tích thống kê về giá trị thiếu
    return {
        "rows_with_at_least_one_missing": missing_rows, # Số dòng chứa ít nhất một ô trống
        "rows_with_at_least_one_missing_ratio": percentage(missing_rows, rows), # Tỉ lệ phần trăm dòng lỗi
        "per_column": per_column, # Toàn bộ thống kê chi tiết theo cột
        "top_missing_columns": [ # Danh sách top 10 cột bị thiếu hụt dữ liệu nghiêm trọng nhất
            {"column": column, **stats} for column, stats in sorted_columns[:10]
        ],
    }
