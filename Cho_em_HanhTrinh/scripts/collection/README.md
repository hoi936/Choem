# Pipeline nhập tư liệu CHO EM

Chạy từ thư mục dự án. Python 3.9+; các lệnh xử lý JSON dùng thư viện chuẩn.
Nhập ảnh cần Pillow để giải mã và kiểm tra file thật. Pipeline không gửi yêu cầu mạng,
không đọc cookie hoặc thông tin đăng nhập. Dữ liệu xuất Facebook chính thức do quản trị
viên cung cấp là đầu vào ưu tiên.

```bash
python3 scripts/collection/archive.py init
python3 scripts/collection/archive.py status
python3 scripts/collection/archive.py discover --file research/permitted_urls.txt
python3 scripts/collection/archive.py import-export /path/to/your_posts_1.json --format facebook
python3 scripts/collection/archive.py import-export /path/to/normalized.json --format normalized
python3 scripts/collection/archive.py import-media 'Ảnh/Anh1.jpg'
python3 scripts/collection/archive.py import-media /path/to/photo.jpg --post-id post_ID --source-url 'https://example.org/original.jpg'
```

Trên Windows dùng `python` thay `python3` nếu cần. Có thể đặt `--root PATH` **trước**
tên lệnh để chạy trên một kho khác. Khi thử nghiệm, luôn dùng thư mục tạm riêng:

```bash
python3 scripts/collection/archive.py --root /tmp/cho-em-test init
python3 -m unittest discover -s scripts/validation -p 'test_archive.py' -v
```

`init` tạo cây thư mục lõi và các JSON rỗng còn thiếu; không tạo mùa mẫu, không ghi
đè dữ liệu đã có. Mảng `[]` có nghĩa là **chưa có bản ghi**, không chứng minh rằng
dự án không có mùa hoặc không có bài viết. Các tài liệu nghiên cứu/báo cáo phải do
người nghiên cứu bổ sung dựa trên bằng chứng.

`discover` nhận URL Facebook được phép ghi nhận từ đối số hoặc file UTF-8, mỗi dòng
một URL; dòng bắt đầu `#` được bỏ qua. Có thể dùng `--source-url URL` để lưu nơi phát
hiện. Lệnh chỉ ghi hàng đợi, không mở URL. URL Facebook được chuẩn hóa, loại tracking;
story/permalink có cùng Facebook ID được đưa về cùng URL. Các cờ `pipeline` giữ tiến
độ phát hiện, trích nội dung, tải media, phân mùa, xác minh. Nhập một ảnh không đủ
chứng minh tất cả media của bài đã được tải nên không tự bật `media_downloaded`.

`import-export` hỗ trợ:

- Mảng JSON của bài xuất hoặc object có `posts`, `your_posts_v2`, `posts_v2`.
- Bài chuẩn hóa có `post_url`, `facebook_post_id`, `published_at`, `caption_original`,
  `caption_completeness`, các mảng quan hệ `season_ids`, `program_ids`, `journey_ids`.
- Facebook JSON: `timestamp` và `data[].post`; dùng `--format facebook` khi đầu vào
  là mảng không có envelope cho biết định dạng. Không lấy mô tả attachment thay caption.

Caption giữ nguyên Unicode, emoji, dấu câu và xuống dòng; chỉ `caption_clean` được
rút gọn khoảng trắng. `complete` biểu thị adapter đã giữ đầy đủ trường caption từ
đầu vào nhận được, không xác minh nguồn Facebook hiện tại hay mức bao phủ lịch sử.
Adapter Facebook chỉ tự ghi `complete` cho `data[].post` khi định dạng đã xác định.
Đầu vào chuẩn hóa/không xác định mặc định `unknown`; nguồn có dấu hiệu cắt ngắn phải
ghi `partial`. `--caption-completeness` cho phép người nhập khai báo trạng thái sau
khi đã kiểm tra nguồn. Caption thiếu luôn là `null` và `unknown`.

File xuất nguyên byte được lưu tại `data/raw/imports/<sha256>.json`; mỗi bài có
`provenance` trỏ file và vị trí entry. Không tự sửa mojibake của bản xuất Meta vì có
thể làm sai Unicode; nếu bản xuất hiển thị lỗi, cần chuẩn hóa riêng có ghi provenance.
ID ổn định ưu tiên Facebook ID, URL rồi dấu vân tay nội dung/thời gian/ID xuất.
Nếu không có ID/URL thì caption thay đổi có thể tạo bản mới cần đối chiếu thủ công.
Nguồn xung đột caption cùng ID không ghi đè caption cũ; được lưu trong
`research/import_conflicts.json` cùng bản xuất mới. Trạng thái xác minh và biên tập
đã có được giữ nguyên. Không tự phân mùa bằng ngày đăng; chỉ chấp nhận ID mùa,
chương trình, chuyến đi đã tồn tại trong processed. Tệp JSON từng bài nằm trong
`data/raw/posts/`; dữ liệu chưa phân mùa đồng bộ vào `data/unclassified/posts.json`.

`import-media` chỉ nhận ảnh local và kiểm tra ảnh giải mã được; không tải URL. Bản
gốc giữ nguyên byte tại `assets/originals/images/<sha256>.<ext>`, trùng byte chỉ lưu
một file nhưng hợp nhất mọi quan hệ nguồn và bài viết. Không dùng nhận dạng khuôn mặt.
`download_status=local_imported` và `downloaded_at=null` phân biệt ảnh local với tải
Facebook. Metadata được ghi vào `data/raw/photos.json`, `processed/media_index.json`,
`unclassified/media.json`; `--post-id` đồng thời nối `post.photo_ids`.

Quyền sử dụng mặc định `unknown`, quyền riêng tư luôn cần kiểm duyệt trước công bố.
Nếu có bằng chứng, dùng `--rights-status permission_confirmed|owned|licensed`
kèm `--rights-evidence 'mô tả hoặc đường dẫn bằng chứng'`. Không coi URL công khai
hoặc quyền truy cập bản xuất là quyền tái xuất bản. Khi nhập lại một ảnh đã có,
trạng thái quyền cũ được giữ để tránh tự đổi quyết định kiểm duyệt; người phụ trách
cần rà soát và cập nhật quyết định có bằng chứng riêng.

Các cập nhật chỉ mục dùng thay file nguyên tử; khóa hệ điều hành ngăn hai tiến
trình CLI cùng ghi. `research/collection_progress.json` và log lưu lần hoàn tất
gần nhất. Khóa tự nhả khi tiến trình dừng. Nếu dừng giữa các file, chạy lại cùng lệnh
để đồng bộ quan hệ và chỉ mục, không nhập trùng. Không có giao dịch nguyên tử cho
toàn bộ nhiều file; nên sao lưu kho trước các thay đổi phân loại/xác minh thủ công.
Quy trình không tự công bố dữ liệu và không xây website.

## Nhập ảnh công khai từ manifest có bằng chứng

`download_public_media.py` chỉ nhận các URL HTTPS trên `fbcdn.net` hoặc miền con,
được ghi rõ trong một manifest JSON. Không sửa tham số URL/ký số, không thêm cookie,
không theo redirect, không thử lại tự động. Mỗi nguồn cần một snapshot đã lưu trong
kho làm provenance. Ví dụ dưới đây chỉ mô tả schema, không phải dữ liệu đã thu thập:

```json
[
  {
    "source_url": "https://scontent.example.fbcdn.net/explicit-original.jpg?signature=UNCHANGED",
    "source_post_url": "https://www.facebook.com/OWNER/posts/POST",
    "description": null,
    "rights_status": "unknown",
    "provenance_snapshot": "research/sources/public_snapshot.html"
  }
]
```

Kiểm tra manifest không truy cập mạng trước khi tải:

```bash
PYTHONPATH=.tools/python python3 scripts/collection/download_public_media.py --manifest research/media_manifest.json --dry-run
PYTHONPATH=.tools/python python3 scripts/collection/download_public_media.py --manifest research/media_manifest.json
```

Script giới hạn 50 MiB mỗi response, ít nhất ba giây giữa hai lần bắt đầu request,
kiểm tra Pillow trước khi thêm ảnh, và dùng cùng kho ảnh gốc/hash của `archive.py`.
HTTP 401/403/407/429, redirect, login hoặc CAPTCHA dừng cả manifest để người nghiên
cứu xem lại quyền truy cập. File đã có, đúng hash và đúng URL nguồn được dùng lại
khi chạy tiếp. Mọi attempt ghi tại `research/download_attempts.json`; lỗi cũng vào
`logs/errors.log`. Không tự bật cờ toàn bộ media của một bài đã thu đủ. Metadata ảnh
có `download_status=downloaded`, thời điểm tải và `retrievals` liên kết snapshot kèm
SHA-256. Quyền tái sử dụng vẫn chưa được xác minh, cần duyệt quyền riêng tư trước
khi xuất bản. Đầu vào từ snapshot công khai không chứng minh mức bao phủ toàn bộ ảnh.
