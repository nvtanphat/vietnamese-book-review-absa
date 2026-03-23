from __future__ import annotations

from typing import Any, Mapping, Sequence

from .helpers import detect_label_columns, percentage, to_dataframe


def scan(records: Sequence[Mapping[str, Any]], text_column: str | None = None) -> dict[str, Any]:
    """Phân tích sự phân bổ và chất lượng của các cột nhãn (labels) như sentiment, rating."""
    # Xử lý trường hợp không có dữ liệu đầu vào
    if not records:
        return {
            "label_columns": [],
            "columns": {},
        }

    # Chuyển đổi dữ liệu sang DataFrame để sử dụng các hàm thống kê của Pandas
    df = to_dataframe(records)
    # Tự động nhận diện các cột đóng vai trò làm nhãn dựa trên tên cột
    label_columns = detect_label_columns(records)
    columns: dict[str, Any] = {}

    for column in label_columns:
        series = df[column]
        # Chuẩn hóa dữ liệu trong cột nhãn: chuyển về chuỗi và loại bỏ khoảng trắng thừa
        normalized = series.astype("string").str.strip()
        # Tạo mặt nạ đánh dấu các dòng bị thiếu nhãn (null, trống, hoặc các từ khóa đại diện rỗng)
        missing_mask = series.isna() | normalized.isna() | normalized.isin(["", "null", "none", "nan"])
        # Đếm tần suất xuất hiện của mỗi giá trị nhãn (chỉ tính các dòng không bị thiếu)
        value_counts = normalized[~missing_mask].value_counts(dropna=False)
        
        total = int(len(df)) # Tổng số lượng bản ghi
        missing = int(missing_mask.sum()) # Tổng số bản ghi bị thiếu nhãn
        non_missing = total - missing # Số lượng bản ghi có nhãn hợp lệ
        
        # Lấy ra danh sách 10 nhãn phổ biến nhất để thống kê
        most_common = value_counts.head(10)
        # Lấy số lượng của nhãn ít nhất và nhiều nhất (dành cho tính toán độ mất cân bằng)
        min_non_zero = int(value_counts[value_counts > 0].min()) if not value_counts.empty else 0
        max_non_zero = int(value_counts.max()) if not value_counts.empty else 0

        # Lưu trữ các thông số phân tích chi tiết cho từng cột nhãn
        columns[column] = {
            "missing_count": missing, # Số lượng bị thiếu
            "missing_ratio": percentage(missing, total), # Tỉ lệ % bị thiếu
            "value_counts": [ # Thống kê chi tiết từng giá trị nhãn
                {"value": str(value), "count": int(count), "ratio": percentage(int(count), total)}
                for value, count in most_common.items()
            ],
            "non_missing_count": non_missing, # Số lượng nhãn thực tế có được
            # Tỉ lệ mất cân bằng (Imbalance): Nhãn xuất hiện nhiều nhất / Nhãn xuất hiện ít nhất
            "imbalance_ratio": round(max_non_zero / min_non_zero, 4) if min_non_zero else None,
        }

    # Trả về kết quả phân tích tổng hợp các cột nhãn
    return {
        "label_columns": label_columns, # Danh sách các cột được xác định là nhãn
        "columns": columns, # Chi tiết thống kê cho từng cột nhãn
    }
