# Hệ thống Tìm kiếm Tin tức

Hệ thống tự động tìm kiếm và tổng hợp tin tức về các công ty, tập trung vào các tin tức tiêu cực.

## Tính năng

- Tìm kiếm tin tức từ NewsAPI
- Tìm kiếm tin tức từ Google Search
- Giao diện web thân thiện với người dùng
- Xuất báo cáo dạng TXT và JSON
- Xử lý đồng thời nhiều nguồn tin
- Lưu trữ lịch sử tìm kiếm

## Yêu cầu hệ thống

- Python 3.8 trở lên
- API key từ NewsAPI (https://newsapi.org)

## Cài đặt

1. Clone repository:
```bash
git clone <repository-url>
cd <repository-name>
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

4. Tạo file .env và thêm API key:
```bash
cp .env.example .env
# Chỉnh sửa file .env và thêm NEWS_API_KEY của bạn
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

3. Nhập tên công ty cần tìm kiếm và nhấn nút "Tìm kiếm"

4. Kết quả sẽ được hiển thị trên giao diện web và có thể tải về dưới dạng TXT hoặc JSON

## Cấu trúc thư mục

```
.
├── app.py              # File chính của ứng dụng
├── requirements.txt    # Danh sách các thư viện cần thiết
├── .env               # File cấu hình môi trường
├── templates/         # Thư mục chứa các template HTML
│   └── index.html     # Template chính
└── reports/          # Thư mục lưu trữ các báo cáo
```

## Lưu ý

- Đảm bảo có API key hợp lệ từ NewsAPI
- Có thể điều chỉnh danh sách từ khóa tiêu cực trong file app.py
- Các báo cáo được lưu tự động trong thư mục reports/
- Log được lưu trong file app.log

## Đóng góp

Mọi đóng góp đều được chào đón. Vui lòng tạo issue hoặc pull request để đóng góp vào dự án. 