# Báo cáo media

Snapshot trang Facebook cho 32 ID ảnh riêng biệt. Kho ảnh có 49 file thực sự tải từ Facebook: 32 bản ưu tiên theo ID ảnh và 17 phiên bản kích thước khác được giữ nguyên; 1 ảnh nhập từ thư mục có sẵn, 0 bản ghi chưa có file. 17 URL bản độ phân giải cao hơn được ghi ở `research/media_upgrade_manifest.json`. Mùa 7 có 15 ảnh riêng biệt được liên kết qua bản ưu tiên; 15 ảnh đã tải. Bài recap hiển thị chỉ số album 43 nhưng snapshot không cung cấp 43 ID/file gốc; không dùng số này làm số ảnh đã tải. 1 Reel có URL, file video tải: 0.

Mỗi ảnh đã tải có `sha256`, kích thước và đường dẫn local; `scripts/validation/validate_archive.py` kiểm tra hash và khả năng giải mã. Không tự thay chữ ký URL, không tải media khi CDN báo chặn. Số lỗi URL trong phiên mạng: 0; xem `research/download_attempts.json`. Tất cả ảnh/video vẫn chờ duyệt quyền và riêng tư.
