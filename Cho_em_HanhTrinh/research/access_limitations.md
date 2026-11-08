# Giới hạn truy cập

Phiên công khai không đăng nhập truy cập đúng trang Facebook và lấy được một số bài. Sau 2 lượt cuộn, trang hiện hộp thoại đăng nhập; collector dừng với trạng thái `stopped_dialog_requires_user_action`. Snapshot và nhật ký ở `research/sources/public_feed_20261018T113355/`. Không truy cập CAPTCHA, không dùng cookie hay tài khoản của người khác.

Các URL bài đã hiện được mở trực tiếp qua giao diện công khai: 7 bài có caption đầy đủ trong JSON được lưu. Không thể xác nhận tổng số bài và khoảng cũ nhất. Ảnh tải từ CDN chỉ dùng URL đã có trong snapshot, không thay chữ ký URL; nếu lỗi truy cập, giữ metadata và yêu cầu bản xuất được cấp hợp lệ.
