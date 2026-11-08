# Bàn giao kho tư liệu & Website Hành Trình CHO EM

Kho này lưu trữ toàn bộ tư liệu lịch sử và trang web giới thiệu dự án **CHO EM** (Facebook ID: `100094610840245`, https://www.facebook.com/profile.php?id=100094610840245), đã được tích hợp đầy đủ từ bộ dữ liệu xuất chính thức của Meta (`D:\CHO_EM\Data_fb`).

## Kết quả có bằng chứng (Đã tích hợp đầy đủ 7 mùa: 2023 – 2026)

- **7 mùa xác minh trực tiếp (Mùa 1 – Mùa 7):**
  - **Mùa 1 (07–08/2023):** *Sân Chơi Cho Em* — Điểm trường Bản Ho Le & Tà Rùng, Trường Mầm non Húc, xã Húc, huyện Hướng Hóa (15/08/2023).
  - **Mùa 2 (01–02/2024):** *Răng Xinh Cho Em* — Trường TH&THCS Triệu Vân, huyện Triệu Phong (02/02/2024).
  - **Mùa 3 (07–08/2024):** *Sân Chơi Cho Em (Mùa 3)* — Điểm trường Chênh Vênh & Hướng Choa, Trường Mầm non Hướng Phùng, huyện Hướng Hóa (06/08/2024).
  - **Mùa 4 (12/2024–01/2025):** *Phao Xinh Cho Em* — Trường TH&THCS Triệu Vân, huyện Triệu Phong (22/01/2025).
  - **Mùa 5 (07–08/2025):** *An Toàn Cho Em* — Trường TH&THCS Tân Thành, huyện Hướng Hóa (11/08/2025).
  - **Mùa 6 (12/2025–02/2026):** *An Toàn Cho Em 2* — Trường PTDTBT Tiểu học Vĩnh Ô, xã Vĩnh Ô, huyện Vĩnh Linh (09/02/2026).
  - **Mùa 7 (07–08/2026):** *Hành Trang Cho Em* — Trường Tiểu học Tà Long (điểm trường thôn Pa Hy), xã Tà Long, huyện Đakrông (18/08/2026).
- **135 bài viết đã chọn lọc và lưu trữ** (từ 142 mục trong `profile_posts_1.html`, đã lọc 5 mục chỉ chia sẻ liên kết trống, 1 bài trùng lặp và 1 trạng thái trống).
- **563 bức ảnh có file gốc cục bộ** (`assets/originals/images/<sha256>.<ext>`, bao gồm 562 ảnh từ bản xuất Facebook + 1 ảnh workspace ban đầu `Ảnh/Anh1.jpg`).
- **7 thước phim tư liệu & recap chính thức** (`assets/originals/videos/<sha256>.mp4`) với đầy đủ thông số kỹ thuật (`width`, `height`, `duration_seconds`, `sha256`).

## Cấu trúc dữ liệu & Website

1. **Dữ liệu gốc & đã xử lý (`data/`):**
   - Bảng gốc: `data/raw/posts.json`, `data/raw/posts/<post_id>.json`, `data/raw/photos.json`, `data/raw/videos.json`, `data/raw/albums.json`, `data/raw/page_info.json`.
   - Bảng tổng hợp: `data/processed/project_info.json`, `data/processed/seasons.json`, `data/processed/programs.json`, `data/processed/journeys.json`, `data/processed/milestones.json`, `data/processed/stories.json`, `data/processed/timeline.json`, `data/processed/featured_content.json`, `data/processed/media_index.json`.
   - Hồ sơ từng mùa: `data/seasons/season_01` đến `data/seasons/season_07`.
2. **Scripts xử lý & kiểm định (`scripts/`):**
   - `scripts/processing/build_full_seasons_archive.py`: Bóc tách, chọn lọc, phân loại 7 mùa từ `D:\CHO_EM\Data_fb` và chuẩn hóa toàn bộ bảng dữ liệu.
   - `scripts/processing/export_website_data.py`: Xuất gói dữ liệu `website/data/archive_bundle.js` phục vụ giao diện web.
   - `scripts/validation/validate_archive.py`: Kiểm định tính toàn vẹn dữ liệu, liên kết chéo và SHA-256 (`0 error`).
3. **Website giới thiệu hành trình (`index.html` & `website/`):**
   - Mở trực tiếp `index.html` trên trình duyệt (không cần server nhờ `website/data/archive_bundle.js`) để khám phá câu chuyện khởi nguồn, ý nghĩa tên gọi, hành trình 7 mùa, câu chuyện tiêu biểu, rạp phim tư liệu, dòng thời gian và kho lưu trữ 563 ảnh + 135 bài viết.
