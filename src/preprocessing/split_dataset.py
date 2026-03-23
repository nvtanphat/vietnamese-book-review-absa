from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.preprocessing.pipeline import preprocess_dataframe

# Danh sách các đường dẫn file dữ liệu thô (raw) có thể có
INPUT_CANDIDATES = (
    Path("data/raw/tiki-book-review.json"),
    Path("data/raw/tiki-book-review.csv"),
)
# Tự động tìm và chọn file đầu tiên tồn tại trong danh sách ứng viên
INPUT = next((path for path in INPUT_CANDIDATES if path.exists()), INPUT_CANDIDATES[0])

# Đường dẫn lưu trữ tập huấn luyện (train) và kiểm tra (test) ở các giai đoạn khác nhau
RAW_INTERIM_TRAIN_OUT = Path("data/interim/raw_train/train.json")
RAW_INTERIM_TEST_OUT = Path("data/interim/raw_test/test.json")
INTERIM_TRAIN_OUT = Path("data/interim/train/train.json")
INTERIM_TEST_OUT = Path("data/interim/test/test.json")
PROCESSED_TRAIN_OUT = Path("data/processed/train_clean.json")
PROCESSED_TEST_OUT = Path("data/processed/test_clean.json")

LABEL = "sentiment_llm" # Cột chứa nhãn cảm xúc (sentiment)
TEXT_COLUMN = "content" # Cột chứa nội dung văn bản đánh giá
TEST_SIZE = 0.2 # Tỉ lệ phân chia tập kiểm tra (20%)

# Các trường thông tin cần giữ lại sau khi xử lý xong
KEEP_COLUMNS = [
    'review_id', 'rating', 'review_title', 'product_name', 'category',
    'content', 'content_raw', 'sentiment_llm', 'as_content', 'as_physical',
    'as_price', 'as_packaging', 'as_delivery', 'as_service',
]
RANDOM_STATE = 42 # Đảm bảo tính nhất quán (reproducibility) khi chia tập dữ liệu


def _write_split(frame: pd.DataFrame, output_path: Path) -> None:
    """Hàm hỗ trợ: Tạo thư mục nếu chưa có và lưu DataFrame ra file JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_json(output_path, orient="records", force_ascii=False, indent=2)


def main() -> None:
    """Quy trình chính: Đọc dữ liệu, lọc nhãn, chia tập dữ liệu thô và tập dữ liệu sạch."""
    # Bước 1: Đọc dữ liệu từ file được chọn
    df = pd.read_json(INPUT) if INPUT.suffix.lower() == ".json" else pd.read_csv(INPUT)
    
    # Bước 2: Lọc bỏ các dữ liệu lỗi hoặc không đủ thông tin nhãn
    df = df[df[LABEL].notna()].copy()
    df[LABEL] = pd.to_numeric(df[LABEL], errors="coerce")
    # Chỉ giữ lại các dòng có nhãn là 0, 1 hoặc 2 (ví dụ: Tiêu cực, Trung tính, Tích cực)
    df = df[df[LABEL].isin([0, 1, 2])].copy()

    # Bước 3: Chia tập dữ liệu THÔ (raw)
    # Sử dụng stratify theo nhãn để đảm bảo tỉ lệ phân bố các lớp là như nhau ở cả 2 tập
    raw_train, raw_test = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df[LABEL],
    )
    raw_train = raw_train.reset_index(drop=True)
    raw_test = raw_test.reset_index(drop=True)

    # Lưu tập dữ liệu chưa xử lý để dùng cho phân tích lỗi hoặc quét dữ liệu (scanning)
    _write_split(raw_train, RAW_INTERIM_TRAIN_OUT)
    _write_split(raw_test, RAW_INTERIM_TEST_OUT)

    # Bước 4: Thực hiện TIỀN XỬ LÝ (Làm sạch văn bản) cho toàn bộ tập dữ liệu
    cleaned = preprocess_dataframe(
        df,
        text_column=TEXT_COLUMN,
        keep_raw=True,
        min_chars=10,
        drop_duplicates=True,
        keep_columns=KEEP_COLUMNS,
    )
    # Chuyển nhãn sang kiểu số nguyên (int) sau khi làm sạch
    cleaned[LABEL] = pd.to_numeric(cleaned[LABEL], errors="coerce").astype(int)

    # Bước 5: Chia tập dữ liệu ĐÃ LÀM SẠCH (Cleaned)
    train, test = train_test_split(
        cleaned,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=cleaned[LABEL],
    )

    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)

    # Lưu kết quả cuối cùng vào các thư mục processed và interim tương ứng
    _write_split(train, INTERIM_TRAIN_OUT)
    _write_split(test, INTERIM_TEST_OUT)
    _write_split(train, PROCESSED_TRAIN_OUT)
    _write_split(test, PROCESSED_TEST_OUT)

    # In kết quả thống kê số lượng bản ghi ra màn hình console
    print(f"raw_train={len(raw_train)}")
    print(f"raw_test={len(raw_test)}")
    print(f"train={len(train)}")
    print(f"test={len(test)}")
    # In ra danh sách file đã được tạo
    print(RAW_INTERIM_TRAIN_OUT)
    print(RAW_INTERIM_TEST_OUT)
    print(INTERIM_TRAIN_OUT)
    print(INTERIM_TEST_OUT)
    print(PROCESSED_TRAIN_OUT)
    print(PROCESSED_TEST_OUT)


if __name__ == "__main__":
    main()
