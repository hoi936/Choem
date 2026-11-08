#!/usr/bin/env python3
"""Write factual handoff documents from the current archive counts and sources."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path, default):
    file = ROOT / path
    return json.loads(file.read_text(encoding='utf-8')) if file.exists() else default


def write(path, text):
    file = ROOT / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text.rstrip() + '\n', encoding='utf-8')


def main():
    posts = read('data/raw/posts.json', [])
    photos = read('data/raw/photos.json', [])
    videos = read('data/raw/videos.json', [])
    seasons = read('data/processed/seasons.json', [])
    programs = read('data/processed/programs.json', [])
    journeys = read('data/processed/journeys.json', [])
    timeline = read('data/processed/timeline.json', [])
    discoveries = read('data/raw/discovered_urls.json', [])
    manifest = read('research/media_manifest.json', [])
    upgrades = read('research/media_upgrade_manifest.json', [])
    variant_groups = read('research/media_variant_groups.json', [])
    attempts = read('research/download_attempts.json', [])
    feed = read('research/sources/public_feed_20261018T113355/index.json', {})
    exact = next((p for p in posts if p.get('facebook_post_id') == '919178351245851'), None)
    link = exact['post_url'] if exact else 'https://www.facebook.com/profile.php?id=100094610840245'
    facebook_downloaded = [p for p in photos if p.get('download_status') == 'downloaded']
    local_imported = [p for p in photos if p.get('download_status') == 'local_imported']
    meta_only = [p for p in photos if not p.get('local_path')]
    season = next((s for s in seasons if s.get('season_id') == 'season_07'), {})
    season_photo_ids = set(season.get('photo_ids', []))
    season_photos = [p for p in photos if p.get('photo_id') in season_photo_ids]
    season_downloaded = [p for p in season_photos if p.get('download_status') == 'downloaded']
    alternate_photos = [p for p in facebook_downloaded if p.get('variant_role') == 'alternate']
    unknown_posts = [p for p in posts if not p.get('season_ids')]
    finished = [p for p in posts if p.get('caption_completeness') == 'complete']
    failed = [a for a in attempts if a.get('status') in ('error','access_stopped')]
    delivered_urls = {purl for p in photos if p.get('download_status') == 'downloaded'
                      for purl in p.get('source_urls', [])}
    actual_failed_urls = {m['source_url'] for m in manifest if m['source_url'] not in delivered_urls
                          and any(a.get('source_url') == m['source_url'] and
                                  a.get('status') in ('error', 'access_stopped') for a in failed)}
    folder = 'data/seasons/season_07'
    fb_page = 'https://www.facebook.com/profile.php?id=100094610840245'
    gdt = 'https://giaoducthoidai.vn/trao-tang-san-choi-cho-cac-chau-mam-non-vung-bien-gioi-quang-tri-post694578.html'
    cdkh = 'https://congdankhuyenhoc.vn/print/trao-tang-cong-trinh-san-choi-cho-em-tren-bien-gioi-huong-phung-179240806121723997.htm'
    season_row = f'| 7 | verified: caption gốc | {sum("season_07" in p.get("season_ids", []) for p in posts)} | {len(season_downloaded)} | 1 | 0 | Thấp; chưa duyệt hết lịch sử mùa |'
    write('README_FOR_NEXT_AGENT.md', f'''# Bàn giao kho tư liệu CHO EM

Kho này phục vụ nghiên cứu dữ liệu cho website tương lai. **Chưa xây website.** Trang được người dùng chỉ định là {fb_page}. Browser công khai xác nhận tên “CHO EM project”, mô tả hướng tới trẻ em Quảng Trị và địa điểm hiển thị Đông Hà, Quảng Trị; xem `data/raw/page_info.json` và snapshot `research/sources/facebook_browser_02.html`.

## Kết quả có bằng chứng

- **1 mùa xác minh trực tiếp:** mùa 7; tổng số mùa đã tồn tại **chưa xác định**. Không tự tạo mùa 1–6 từ số thứ tự 7.
- {len(posts)} bài có URL trực tiếp: {len(finished)} caption gốc đầy đủ, {len(posts)-len(finished)} bài chỉ có đoạn hiển thị hoặc metadata. {len(videos)} Reel có URL và thời lượng hiển thị; chưa có file video.
- {len(photos)} bản ghi ảnh: {len(facebook_downloaded)} file Facebook cho {len(variant_groups)} ảnh riêng biệt (gồm {len(alternate_photos)} bản kích thước khác được giữ để bảo toàn nguồn), {len(local_imported)} ảnh có sẵn trong thư mục gốc và {len(meta_only)} bản ghi chưa có file. `research/media_manifest.json` liệt kê {len(manifest)} ID ảnh ban đầu; `research/media_upgrade_manifest.json` ghi {len(upgrades)} URL bản lớn hơn. Dùng `research/media_variant_groups.json` để chọn bản ưu tiên, tránh đếm hai lần.
- 1 chương trình xác minh: “Hành Trang Cho Em” tại Trường Tiểu học Tà Long ngày 18/8/2026. Hồ sơ nằm ở `{folder}`. Chưa đủ chứng cứ để tạo hồ sơ chuyến đi riêng.

## Cách đọc và nối dữ liệu

Đọc `DATA_DICTIONARY.md` trước. Bảng gốc `data/raw/posts.json`, `photos.json`, `videos.json`; bảng tổng hợp `data/processed/seasons.json`, `programs.json`, `timeline.json`. `post_ids`, `photo_ids`, `program_ids` là khóa liên kết. Mỗi ảnh có `source_urls`, `post_ids`, `season_ids`; ảnh có file chỉ dùng đường dẫn `local_path` sau khi kiểm tra `download_status`. `data/processed/media_index.json` gom ảnh và video. Timeline dùng ngày sự kiện, có mốc đăng bài tách riêng. Nội dung trang chủ chỉ nên lấy từ `data/processed/featured_content.json` sau khi duyệt ảnh; bảng này hiện chưa có lựa chọn được duyệt.

Nguồn chứng minh claim quan trọng nằm ở `research/evidence_map.json`. Caption nguyên văn và Unicode giữ tại `data/raw/posts.json`, đối chiếu được với snapshot bằng `caption_evidence`. `research/facebook_snapshot_extraction.json` lưu kết quả parser; `research/sources/` giữ HTML/nhật ký tìm kiếm. `scripts/collection/archive.py` hỗ trợ nhập bản xuất chính thức có checkpoint; xem `scripts/collection/README.md`.

## Giới hạn và việc cần tiếp nối

Facebook hiện hộp thoại đăng nhập khi cuộn bài cũ; nhật ký `research/sources/public_feed_20261018T113355/index.json` ghi điểm dừng. Chưa thể xác định lịch sử từ ngày đầu, số mùa thực tế, ngày thành lập, ngày bắt đầu/kết thúc mùa 7, đầy đủ album hoặc nội dung của các bài chưa được phát hiện. Hai báo về “Sân chơi cho em” năm 2024 được giữ làm đầu mối ở `research/season_research_findings.json`; chưa có liên kết chắc chắn với Facebook ID trên. Cần bản xuất bài viết và media chính thức từ người quản lý trang để bổ sung phần lịch sử thiếu.

Tất cả media có `rights_status=unknown` và `privacy_review_required=true`; chưa có quyền tái sử dụng trên website được xác nhận. Không dùng dữ liệu riêng tư từ người bình luận. `reports/PRIVACY_RIGHTS_REVIEW.md` ghi công việc kiểm duyệt.
''')
    write('research/source_index.md', f'''# Chỉ mục nguồn

- Trang Facebook được chỉ định và snapshot công khai: {fb_page}; `research/sources/facebook_browser_02.html`, `facebook_browser_02.json`.
- Bài tổng kết mùa 7, caption đầy đủ: {link}; trích xuất offline ở `research/facebook_snapshot_extraction.json`.
- Năm bài viết khác có caption đầy đủ: snapshot `research/sources/known_post_01_*.html` đến `known_post_05_*.html`, trích xuất `research/known_post_*_extraction.json`.
- Reel ngày 17/8/2026: https://www.facebook.com/reel/1411736247503742/ ; snapshot `research/sources/facebook_reel_browser.html` và `research/facebook_reel_extraction.json`.
- Hai bài báo về Hướng Phùng ngày 6/8/2024: {gdt} và {cdkh}; snapshot tại `research/sources/gdtd_20240806_decoded.html`, `cdkh_20240806.html`. Đây là bằng chứng hoạt động báo chí, chưa đủ để gán mùa.
- 16 nhật ký truy vấn: `research/sources/season_search_001.json` đến `season_search_016.json`; chỉ mục tìm kiếm là đầu mối, không thay caption gốc.
- Kiểm kê dữ liệu ban đầu: `research/environment_inventory.json`.
''')
    write('research/season_discovery.md', f'''# Khảo sát mùa

Caption công khai của bài tổng kết ngày 20/8/2026 gọi trực tiếp “mùa 7”; vì vậy mùa 7 được xác minh. Nguồn: {link}. Tổng số mùa thực tế vẫn chưa biết. Các số 1–6 không được ghi thành hồ sơ chỉ từ số thứ tự 7.

Hai bài báo ngày 6/8/2024 nói “năm thứ 3 triển khai” công trình Sân chơi cho em. Cụm này không chứng minh “mùa 3”, cũng không chứng minh mỗi năm một mùa. Link báo lưu tại `research/source_index.md`. Lịch sử trước các bài 2026 không thể duyệt đủ qua phiên Facebook công khai hiện tại.
''')
    write('research/unresolved_questions.md', '''# Câu hỏi chưa giải quyết

1. Trang Facebook có những mùa nào trước mùa 7? Ngày bắt đầu, kết thúc, chủ đề, chương trình và tổng kết của từng mùa là gì?
2. Dự án thành lập khi nào, ý nghĩa tên gọi, sứ mệnh và tầm nhìn chính thức là gì?
3. “Năm thứ 3” trong báo về Hướng Phùng 2024 tính cho toàn dự án hay chuỗi sân chơi? Hoạt động này liên kết thế nào với Facebook ID 100094610840245?
4. Những bài cũ hơn phạm vi hiện thấy có caption gốc và ngày đăng nào? Có bản xuất hợp lệ để kiểm kê đủ không?
5. Trong album recap được hiển thị 43 ảnh, có bao nhiêu ảnh được phép truy cập và tái sử dụng từ bản xuất chính thức?
6. Ai nắm quyền đối với ảnh/video và đã có đồng ý phù hợp để đăng hình trẻ em trên website độc lập chưa?
''')
    write('research/access_limitations.md', f'''# Giới hạn truy cập

Phiên công khai không đăng nhập truy cập đúng trang Facebook và lấy được một số bài. Sau {feed.get('last_scroll','?')} lượt cuộn, trang hiện hộp thoại đăng nhập; collector dừng với trạng thái `{feed.get('status','unknown')}`. Snapshot và nhật ký ở `research/sources/public_feed_20261018T113355/`. Không truy cập CAPTCHA, không dùng cookie hay tài khoản của người khác.

Các URL bài đã hiện được mở trực tiếp qua giao diện công khai: {len(finished)} bài có caption đầy đủ trong JSON được lưu. Không thể xác nhận tổng số bài và khoảng cũ nhất. Ảnh tải từ CDN chỉ dùng URL đã có trong snapshot, không thay chữ ký URL; nếu lỗi truy cập, giữ metadata và yêu cầu bản xuất được cấp hợp lệ.
''')
    write('content/project_story.md', f'''# Giới thiệu CHO EM — bản nghiên cứu

Trang {fb_page} tự giới thiệu là “CHO EM project”, thuộc nhóm tổ chức từ thiện, ở Đông Hà, Quảng Trị và hướng đến trẻ em Quảng Trị. Đây là phần giới thiệu ngắn duy nhất xác minh được trực tiếp từ trang. Chưa đủ bằng chứng về hoàn cảnh ra đời, ý nghĩa tên, người sáng lập hoặc hành trình các mùa trước.

Nguồn gốc: `data/raw/page_info.json`, `research/sources/facebook_browser_02.html`.
''')
    write('content/mission_vision.md', '''# Sứ mệnh và tầm nhìn

Chưa tìm được phát biểu chính thức về sứ mệnh và tầm nhìn dài hạn. Mùa 7 có mục tiêu giáo dục phòng chống tai nạn đuối nước tại Trường Tiểu học Tà Long theo bài tổng kết, nhưng không nên thay thế mục tiêu chương trình này cho sứ mệnh toàn dự án. Xem `data/processed/project_info.json`.
''')
    write('content/complete_history.md', f'''# Lịch sử CHO EM theo bằng chứng hiện có

**Năm 2024 — đầu mối cần đối chiếu.** Hai bài báo ghi nhận Ban Tổ chức dự án Cho Em (Quảng Trị) phối hợp Đồn Biên phòng Hướng Phùng trao công trình sân chơi cho hai điểm trường Hướng Choa và Chênh Vênh ngày 6/8/2024. Báo đưa giá trị khoảng 35 triệu đồng và dẫn lời người tham gia về “năm thứ 3”. Chưa tìm được bài Facebook gốc gắn chính xác sự kiện này với ID trang đã chỉ định, nên hồ sơ giữ dưới dạng đầu mối nghiên cứu. Nguồn: {gdt}; {cdkh}.

**11/8/2026 — bài kêu gọi sách.** Trang đăng lời kêu gọi quyên góp sách trong khuôn khổ Hành Trang Cho Em tại Tà Long. Nguồn và caption đầy đủ nằm trong `research/sources/known_post_05_*.html` và `data/raw/posts.json`.

**17/8/2026 — Reel chuẩn bị.** Trang đăng video về kỳ vọng của các thành viên trước chương trình giáo dục phòng chống đuối nước tại Tà Long. Reel mô tả việc sắp khởi hành; chưa dùng ngày đăng làm ngày khởi hành. Nguồn: https://www.facebook.com/reel/1411736247503742/ .

**18/8/2026 — mốc xác minh trực tiếp.** CHO EM mùa 7 tổ chức Hành Trang Cho Em tại Trường Tiểu học Tà Long, Quảng Trị, giáo dục phòng chống đuối nước và trao 125 suất quà, 125 áo phao, hơn 100 quyển sách, 2 tủ sách. Nguồn: {link}.

**20/8/2026 — bài tổng kết.** Trang đăng recap và nói chặng đường mùa 7 khép lại. Ngày đăng bài không được dùng làm ngày kết thúc mùa. Dữ liệu sau thời điểm này và lịch sử đầy đủ trước đó chưa khảo sát được.
''')
    write('content/seasons_overview.md', f'''# Các mùa đã xác minh

| Mùa | Thời gian xác minh | Chủ đề | Chương trình | Địa điểm | Kết quả có nguồn |
|---|---|---|---|---|---|
| 7 | Hoạt động 18/8/2026; bài tổng kết 20/8/2026. Ngày mở/đóng mùa chưa biết | Chưa xác minh tên chủ đề | Hành Trang Cho Em | Trường Tiểu học Tà Long, Quảng Trị | 125 quà, 125 áo phao, hơn 100 sách, 2 tủ sách |

Nguồn chính: {link}. Ảnh liên quan được nối qua `data/processed/seasons.json` và `data/raw/photos.json`; chưa chọn ảnh bìa để xuất bản vì quyền dùng ảnh chưa được xác nhận. Tổng số mùa chưa biết.
''')
    write('content/featured_stories.md', f'''# Câu chuyện tiêu biểu có nguồn

**Hành Trang Cho Em, mùa 7:** Ngày 18/8/2026, dự án tổ chức hoạt động giáo dục phòng chống đuối nước tại Trường Tiểu học Tà Long và trao các vật phẩm được công bố trong bài tổng kết. Hồ sơ chi tiết: `data/processed/stories.json`; nguồn: {link}. Chưa trích dẫn lời nói, danh tính hoặc hoàn cảnh riêng của trẻ em. Cần duyệt ảnh trước khi đưa lên website.
''')
    write('content/milestones.md', f'''# Dấu mốc đã xác minh

- 18/8/2026: Hành Trang Cho Em tại Trường Tiểu học Tà Long. Nguồn: {link}.
- 20/8/2026: bài tổng kết mùa 7 được đăng. Đây là mốc bài viết, không phải ngày kết thúc mùa được xác minh.

Đầu mối 2024 nằm ở `content/complete_history.md`, chưa có trong timeline đã xác minh của đúng trang Facebook.
''')
    write('content/website_content_plan.md', '''# Kế hoạch dữ liệu cho website tương lai

- **Trang chủ:** có thể dùng tên, mô tả dự án và mốc mùa 7; ảnh hero chờ quyền sử dụng.
- **Về CHO EM:** tên và địa bàn có nguồn; câu chuyện thành lập, sứ mệnh, tầm nhìn cần tài liệu chính thức.
- **Hành trình qua các mùa:** hiện chỉ có mùa 7 xác minh. Không hiển thị mùa 1–6 hoặc dòng thời gian đầy đủ như dữ liệu chắc chắn.
- **Chi tiết mùa 7:** dùng `data/seasons/season_07/` để nối chương trình, bài, timeline, ảnh; ghi rõ phần thiếu.
- **Dấu chân thiện nguyện:** Tà Long có nguồn trực tiếp. Hướng Phùng 2024 giữ là đầu mối chờ xác nhận liên kết dự án.
- **Những câu chuyện và thành tựu:** dùng số liệu được bài tổng kết công bố, kèm URL; không tự tăng quy mô.
- **Thư viện ảnh:** chỉ dùng ảnh có file và đã được duyệt quyền, kiểm tra riêng ảnh có trẻ em; tránh lấy ảnh công khai làm mặc nhiên được phép đăng lại.
- **Đồng hành:** chỉ đăng phương thức liên hệ nếu người quản lý xác nhận còn đúng và muốn công khai trên website mới.

Tài liệu này chỉ chuẩn bị nội dung, không triển khai giao diện.
''')
    write('reports/COLLECTION_REPORT.md', f'''# Báo cáo thu thập — 18/10/2026

Trang chính thức: {fb_page}. Đã lập chỉ mục {len(discoveries)} URL qua nguồn công khai; {len(posts)} bài có URL trực tiếp (trong đó {len(videos)} Reel), {len(finished)} caption đầy đủ, {len(posts)-len(finished)} caption còn thiếu; Reel có metadata nhưng chưa có file video; {len(programs)} chương trình đã xác minh, {len(journeys)} chuyến đi có hồ sơ, {len(timeline)} mốc timeline (gồm các ngày đăng bài). Ảnh Facebook tải thành công: **{len(facebook_downloaded)} file / {len(variant_groups)} ảnh riêng biệt**; trong đó {len(alternate_photos)} file là phiên bản kích thước khác; ảnh sẵn có trên máy được nhập: {len(local_imported)}; ảnh chỉ có metadata: {len(meta_only)}. Không đồng nhất số URL, ID ảnh và file vật lý.

Phạm vi chỉ gồm phần trang Facebook tải được khi không đăng nhập và hai bài báo đối chiếu. Bị giới hạn khi cuộn về bài cũ; `research/access_limitations.md` nêu chi tiết. Chưa biết tổng số bài hay tổng số mùa nên không tính tỷ lệ hoàn thành toàn lịch sử.
''')
    write('reports/SEASON_COVERAGE_REPORT.md', f'''# Mức bao phủ theo mùa

| Mùa | Trạng thái xác minh | Bài đăng đã gán mùa | Ảnh Facebook riêng biệt đã tải | Chương trình | Chuyến đi | Mức độ hoàn chỉnh |
|---|---|---:|---:|---:|---:|---|
{season_row}

Số bài phát hiện có URL: {len(posts)} (gồm Reel); bài có caption hoàn chỉnh: {len(finished)}; bài chờ bổ sung caption: {len(posts)-len(finished)}; bài chưa gán mùa: {len(unknown_posts)}. Ảnh có metadata: {len(photos)} bản ghi file, tương ứng {len(variant_groups)} ảnh Facebook riêng biệt và {len(local_imported)} ảnh nhập từ máy; file Facebook tải thành công: {len(facebook_downloaded)}; lỗi tải có URL khác nhau được ghi nhận: {len(actual_failed_urls)}. Chương trình xác minh: {sum(p.get('verification_status')=='verified' for p in programs)}.

Chỉ mùa 7 có bằng chứng trực tiếp; **tổng số mùa chưa biết**. Đánh giá thấp chỉ áp dụng cho phạm vi đã thấy, vì không thể duyệt các bài cũ hơn nhóm bài đang hiển thị hoặc kiểm kê hết album. Hai bài tri ân chưa gán mùa vì caption không nêu mùa hoặc tên chương trình đã xác minh.
''')
    write('reports/MEDIA_REPORT.md', f'''# Báo cáo media

Snapshot trang Facebook cho {len(manifest)} ID ảnh riêng biệt. Kho ảnh có {len(facebook_downloaded)} file thực sự tải từ Facebook: {len(variant_groups)} bản ưu tiên theo ID ảnh và {len(alternate_photos)} phiên bản kích thước khác được giữ nguyên; {len(local_imported)} ảnh nhập từ thư mục có sẵn, {len(meta_only)} bản ghi chưa có file. {len(upgrades)} URL bản độ phân giải cao hơn được ghi ở `research/media_upgrade_manifest.json`. Mùa 7 có {len(season_photos)} ảnh riêng biệt được liên kết qua bản ưu tiên; {len(season_downloaded)} ảnh đã tải. Bài recap hiển thị chỉ số album 43 nhưng snapshot không cung cấp 43 ID/file gốc; không dùng số này làm số ảnh đã tải. {len(videos)} Reel có URL, file video tải: 0.

Mỗi ảnh đã tải có `sha256`, kích thước và đường dẫn local; `scripts/validation/validate_archive.py` kiểm tra hash và khả năng giải mã. Không tự thay chữ ký URL, không tải media khi CDN báo chặn. Số lỗi URL trong phiên mạng: {len(actual_failed_urls)}; xem `research/download_attempts.json`. Tất cả ảnh/video vẫn chờ duyệt quyền và riêng tư.
''')
    write('reports/MISSING_DATA.md', '''# Dữ liệu còn thiếu

- Danh mục và hồ sơ các mùa trước mùa 7; tổng số mùa chưa xác định.
- Bài thành lập, ý nghĩa tên, sứ mệnh/tầm nhìn, ngày bắt đầu/kết thúc từng mùa.
- Bài đăng cũ hơn phạm vi hiện thấy, kèm caption đầy đủ và thời gian đăng gốc.
- Album đầy đủ, nguồn ảnh gốc khi URL công khai không tải được, video gốc.
- Bằng chứng trực tiếp liên kết hoạt động Hướng Phùng năm 2024 với đúng Facebook ID 100094610840245.
- Bản chấp thuận quyền sử dụng ảnh và đồng ý phù hợp đối với ảnh trẻ em/người thụ hưởng.

Cách bổ sung phù hợp: người quản lý trang cung cấp bản xuất dữ liệu Facebook hợp lệ (bài viết, caption, album/media, thời gian đăng) và tài liệu nội bộ về các mùa/quyền sử dụng. Công cụ nhập tại `scripts/collection/archive.py` có thể chạy tiếp mà không xóa dữ liệu đã xác minh.
''')
    write('reports/PRIVACY_RIGHTS_REVIEW.md', f'''# Rà soát quyền sử dụng và riêng tư

Các {len(photos)} bản ghi ảnh và {len(videos)} video đều được giữ `rights_status=unknown` hoặc cần xem lại, không được coi là đã cấp phép cho website độc lập. Ảnh có trẻ em/người thụ hưởng cần người quản lý xác nhận căn cứ sử dụng và kiểm tra nội dung trước khi xuất bản. Không nhận dạng khuôn mặt hay đoán danh tính từ ảnh. Không đưa thông tin người bình luận vào bảng dữ liệu.

Caption recap chứa thông tin liên hệ và ngân hàng do dự án công khai tại thời điểm đăng; bản gốc chỉ lưu trong kho nghiên cứu. Trước khi đưa lên website cần hỏi người quản lý xem thông tin còn hợp lệ và có muốn công bố trên kênh mới. Các bản HTML gốc có thể chứa nội dung giao diện ngoài bài dự án; chỉ dùng nội bộ nghiên cứu.

Chưa có media nào ở trạng thái `approved_for_publication`. Việc tải thành công chỉ chứng minh file đọc được, không xác lập quyền tái sử dụng.
''')
    print(json.dumps({'reports_written': 17, 'posts': len(posts), 'photos':len(photos),
                      'facebook_downloaded':len(facebook_downloaded)},ensure_ascii=False))


if __name__=='__main__':
    main()
