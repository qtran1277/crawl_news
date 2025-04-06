# Hệ thống Tìm kiếm Tin tức

Hệ thống tự động tìm kiếm và tổng hợp tin tức về các công ty, tập trung vào các tin tức tích cực hoặc tiêu cực.

## Tính năng

- Tìm kiếm tin tức từ Google Search
- Giao diện web thân thiện với người dùng
- Xuất báo cáo dạng TXT và JSON
- Xử lý đồng thời nhiều nguồn tin
- Lưu trữ lịch sử tìm kiếm
- Phân tích cảm xúc (sentiment analysis) cho tin tức
- Hỗ trợ nhiều analyzer (OpenAI, Local LM Studio)
- Giao diện responsive, thân thiện với mobile
- Sidebar có thể thu gọn/mở rộng
- Hiển thị biểu đồ phân bố cảm xúc
- Phân loại tin tức theo cảm xúc (tích cực/trung lập/tiêu cực)

## Yêu cầu hệ thống

- Python 3.8 trở lên
- API key từ OpenAI (nếu sử dụng OpenAI Analyzer)
- LM Studio (nếu sử dụng Local Analyzer)

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/tranquang/Crawl_news_v2.git
cd Crawl_news_v2
```

2. Tạo môi trường ảo và kích hoạt:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

3. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

4. Tạo file .env và thêm API keys:
```bash
cp .env.example .env
# Chỉnh sửa file .env và thêm:
OPENAI_API_KEY=your_api_key_here
```

## Sử dụng

1. Khởi động ứng dụng:
```bash
python app.py
```

2. Mở trình duyệt và truy cập:
```
http://localhost:5000
```

3. Cấu hình Analyzer:
   - Nhấn nút "Cài đặt Analyzer" để chọn loại analyzer
   - Có thể chọn giữa OpenAI hoặc Local LM Studio
   - Lưu cài đặt để sử dụng cho các lần tìm kiếm sau

4. Tìm kiếm tin tức:
   - Nhập từ khóa tìm kiếm
   - Chọn khoảng thời gian
   - Chọn số lượng kết quả tối đa
   - Nhấn "Tìm kiếm"

5. Xem kết quả:
   - Kết quả được phân loại theo cảm xúc
   - Biểu đồ phân bố cảm xúc
   - Có thể tải về dưới dạng TXT hoặc JSON
   - Xem lịch sử tìm kiếm trong sidebar

## Cấu trúc thư mục

```
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
├── static/
├── templates/
├── reports/          # Thư mục lưu trữ các báo cáo
├── logs/            # Thư mục lưu trữ log files
├── tests/           # Thư mục chứa các file test
├── drivers/         # Thư mục chứa web drivers
├── app.py          # File chính của ứng dụng
├── run.py          # File khởi chạy ứng dụng
├── database.py     # File xử lý database
├── requirements.txt # Danh sách các thư viện cần thiết
├── .env            # File cấu hình môi trường
├── .env.example    # File mẫu cho .env
└── news_search.db  # SQLite database
```

## Lưu ý

- Nếu sử dụng OpenAI Analyzer, cần có API key từ OpenAI
- Nếu sử dụng Local Analyzer, cần cài đặt và chạy LM Studio
- Các báo cáo được lưu tự động trong thư mục reports/
- Log được lưu trong thư mục logs/ và file app.log
- Lịch sử tìm kiếm được lưu trong SQLite database (news_search.db)

## Đóng góp

Mọi đóng góp đều được chào đón. Vui lòng tạo issue hoặc pull request để đóng góp vào dự án. 