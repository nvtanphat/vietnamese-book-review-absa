from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from .helpers import count_emojis, percentage, to_text


def scan(records: Sequence[Mapping[str, Any]], text_column: str | None = None) -> dict[str, Any]:
    """Phân tích sự hiện diện và thống kê tần suất của các biểu tượng cảm xúc (emoji) trong văn bản."""
    # Xử lý trường hợp dữ liệu rỗng hoặc không chỉ định cột văn bản cần quét
    if not records or not text_column:
        return {
            "text_column": text_column,
            "rows_with_emoji": 0,
            "rows_with_emoji_ratio": 0.0,
            "emoji_total": 0,
            "top_emojis": [],
            "emoji_samples": [],
        }

    emoji_counter: Counter[str] = Counter() # Dùng để đếm số lần xuất hiện của từng loại emoji
    samples: list[str] = [] # Danh sách chứa một vài ví dụ về các emoji tìm thấy
    rows_with_emoji = 0 # Đếm tổng số dòng (records) có chứa ít nhất một emoji

    # Duyệt qua từng dòng dữ liệu để tìm emoji
    for row in records:
        text = to_text(row.get(text_column))
        # Sử dụng hàm phụ trợ helpers.count_emojis để trích xuất danh sách emoji
        emojis = count_emojis(text)
        if emojis:
            rows_with_emoji += 1
            # Lấy mẫu một vài emoji đầu tiên tìm được (tối đa 10 mẫu)
            if len(samples) < 10:
                samples.extend(emojis[: max(0, 10 - len(samples))])
        # Cập nhật số lượng đếm được vào bộ đếm tổng
        emoji_counter.update(emojis)

    # Trả về báo cáo thống kê chi tiết về emoji
    return {
        "text_column": text_column,
        "rows_with_emoji": rows_with_emoji, # Số dòng có sự xuất hiện của emoji
        "rows_with_emoji_ratio": percentage(rows_with_emoji, len(records)), # Tỉ lệ phần trăm dòng có emoji
        "emoji_total": sum(emoji_counter.values()), # Tổng số lượng emoji đếm được trên toàn bộ tập dữ liệu
        "all_emojis": [ # Danh sách tất cả emoji và số lần xuất hiện tương ứng, sắp xếp từ nhiều đến ít
            {"emoji": emoji, "count": count}
            for emoji, count in emoji_counter.most_common()
        ],
        "emoji_samples": samples, # Một vài emoji thực tế làm ví dụ
    }
