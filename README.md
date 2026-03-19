# Phân Tích Cảm Xúc Đa Khía Cạnh (ABSA) - Review Sách Tiki

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-PyTorch-red.svg)](https://pytorch.org/)
[![Model](https://img.shields.io/badge/Model-PhoBERT-orange.svg)](https://huggingface.co/vinai/phobert-base-v2)
[![Dataset](https://img.shields.io/badge/Dataset-Kaggle-blue.svg)](https://www.kaggle.com/datasets/phtnguyn1ytj/tiki-book-reviews)

Dự án nghiên cứu và triển khai hệ thống **Phân tích Cảm xúc Đa khía cạnh (Aspect-Based Sentiment Analysis - ABSA)** dựa trên dữ liệu đánh giá sách từ nền tảng thương mại điện tử Tiki. Sử dụng mô hình ngôn ngữ **PhoBERT** để đồng thời phân loại cảm xúc chung và 6 khía cạnh cụ thể của sản phẩm.

## 🚀 Tính Năng Chính
- **Pipeline Tiền Xử Lý Chuyên Sâu:** Chuẩn hóa Unicode, xử lý Emoji, loại bỏ nhiễu (URL, Email, SĐT), xử lý Teencode và ký tự lặp.
- **Phân Tích Đa Khía Cạnh:** Phân loại cảm xúc (Tích cực, Trung lập, Tiêu cực) trên 6 khía cạnh:
  - `Content`: Nội dung sách.
  - `Physical`: Chất lượng giấy, bìa, in ấn.
  - `Price`: Giá cả.
  - `Packaging`: Quy cách đóng gói.
  - `Delivery`: Dịch vụ giao hàng.
  - `Service`: Chăm sóc khách hàng.
- **Deep Learning Model:** Fine-tune mô hình `vinai/phobert-base-v2` với Focal Loss để xử lý mất cân bằng dữ liệu.
- **Dashboard Trực Quan:** Tích hợp Streamlit Dashboard để theo dõi thống kê và kiểm tra kết quả tiền xử lý.

## 📁 Cấu Trúc Thư Mục
```text
DoAn2/
├── data/                   # Quản lý dữ liệu đa phiên bản (Raw, Interim, Processed)
├── src/                    # Logic lõi (Preprocessing, Balancing, Analysis)
├── notebooks/              # Các bước thực nghiệm EDA, Training PhoBERT
├── scripts/                # Script tiện ích (Crawler, Converter)
├── experiments/            # Lưu trữ model checkpoints và metrics
├── dashboard.py            # Giao diện visualization dữ liệu
└── requirements.txt        # Thư viện cần thiết
```

## 🛠 Hướng Dẫn Cài Đặt
1. **Clone project:**
   ```bash
   git clone https://github.com/nvtanphat/vietnamese-book-review-absa.git
   cd vietnamese-book-review-absa
   ```
2. **Cài đặt môi trường:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Dữ liệu:**
   Tải bộ dữ liệu đã làm sạch tại [Kaggle Dataset](https://www.kaggle.com/datasets/phtnguyn1ytj/tiki-cleaned-book-reviews) và giải nén vào thư mục `data/processed/`.

## 📊 Mô Hình (PhoBERT)
Mô hình sử dụng kiến trúc `RobertaForSequenceClassification` với 27 đơn vị đầu ra (3 nhãn Sentiment + 24 nhãn cho 6 khía cạnh). 
- **Max Length:** 128
- **Batch Size:** 16
- **Epochs:** 4

## 👨‍💻 Tác Giả
- **Phat Nguyen** (@nvtanphat)

## 📄 Giấy Phép
Dự án được phân phối dưới giấy phép MIT.
