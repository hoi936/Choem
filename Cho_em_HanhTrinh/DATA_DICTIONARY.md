# Từ điển dữ liệu CHO EM

Tài liệu mô tả định dạng do `scripts/collection/archive.py` nhập và `scripts/validation/validate_archive.py` kiểm tra. Tất cả đường dẫn bên dưới tính từ thư mục dự án. Dữ liệu JSON dùng UTF-8; khóa tiếng Anh, nội dung biên tập tiếng Việt.

Một file `[]` nghĩa là chưa có bản ghi đáp ứng điều kiện để nhập, không chứng minh rằng thực tế không có mùa, bài viết hay hoạt động. Các cấu trúc chưa có bản ghi được mô tả để tiếp tục nghiên cứu; không phải dữ liệu mẫu hoặc sự kiện đã xảy ra.

## Quy ước chung

| Quy ước | Ý nghĩa |
|---|---|
| `null` | Chưa biết giá trị; không thay bằng ngày, địa điểm hoặc con số giả định. |
| `[]` trong quan hệ | Chưa có liên kết đã xác định; không tự tạo thực thể để lấp chỗ trống. |
| `verification_status: verified` | Khẳng định có bằng chứng trực tiếp được đối chiếu. URL tồn tại tự nó chưa chứng minh khẳng định. |
| `verification_status: inferred` | Có căn cứ suy luận nhưng chưa được nguồn xác nhận trực tiếp. |
| `verification_status: unknown` | Chưa đủ bằng chứng. |
| `source_status` | Cách tiếp cận hoặc tình trạng nguồn; tách biệt mức xác minh nội dung. |
| `source_urls` | Nguồn công khai để đối chiếu; ưu tiên URL trực tiếp. |
| `research_notes` | Lý do phân loại, thông tin còn thiếu hoặc giới hạn nguồn. |
| Đường dẫn | Tương đối so với thư mục dự án, dấu `/`; không chứa cookie hay thông tin đăng nhập. |
| SHA-256 | Chuỗi hex 64 ký tự tính trên byte gốc, không tính trên bản văn bản đã chuẩn hóa. |

Các ID là chuỗi ổn định. Không lấy thứ tự trong mảng hoặc tên file ảnh làm bằng chứng lịch sử. Chỉ tạo thư mục mùa khi có bằng chứng mùa tồn tại; không suy một năm tương ứng một mùa và không tự tạo mùa 1–6 chỉ vì phát hiện mùa 7.

## Danh mục file và kiểu dữ liệu gốc

| File | Kiểu JSON | Khóa định danh / chức năng |
|---|---|---|
| `data/raw/page_info.json` | object | `page_id`, thông tin nguồn Facebook chính thức. |
| `data/raw/posts.json` | array of objects | `post_id`, chỉ mục bài đăng chính. |
| `data/raw/posts/<post_id>.json` | object | Bản tra cứu từng bài, cùng nội dung với chỉ mục chính. |
| `data/raw/photos.json` | array of objects | `photo_id`, metadata ảnh và đường dẫn file thật. |
| `data/raw/videos.json` | array of objects | `video_id`, video hoặc metadata nguồn. |
| `data/raw/albums.json` | array of objects | `album_id`, album được xác định từ nguồn. |
| `data/raw/discovered_urls.json` | array of objects | `discovery_id`, hàng đợi URL và trạng thái xử lý. |
| `data/raw/imports/<sha256>.json` | array or object theo nguồn | Bản export nguyên byte; không ép thành schema biên tập. |
| `data/processed/project_info.json` | object | `project_id`, hồ sơ dự án có phân biệt điều đã biết/chưa biết. |
| `data/processed/seasons.json` | array of objects | `season_id`, chỉ các mùa có dấu hiệu/bằng chứng thực. |
| `data/processed/programs.json` | array of objects | `program_id`, chương trình/hoạt động có nguồn. |
| `data/processed/journeys.json` | array of objects | `journey_id`, chuyến đi có nguồn. |
| `data/processed/timeline.json` | array of objects | `event_id`, sự kiện theo ngày diễn ra; chấp nhận `timeline_id` cho adapter cũ. |
| `data/processed/milestones.json` | array of objects | `milestone_id`, dấu mốc có bằng chứng. |
| `data/processed/stories.json` | array of objects | `story_id`, nội dung biên tập liên kết nguồn. |
| `data/processed/featured_content.json` | array of objects | Gợi ý sử dụng nội dung; không đồng nghĩa được duyệt xuất bản. |
| `data/processed/media_index.json` | array of objects | `media_id`, `media_type`, chỉ mục hợp nhất media. |
| `data/unclassified/posts.json` | array of objects | Các bài chưa liên kết mùa, không phải bài bị loại bỏ. |
| `data/unclassified/media.json` | array of objects | Media chưa liên kết mùa. |
| `research/evidence_map.json` | array of objects | Các khẳng định và bằng chứng. |
| `research/collection_progress.json` | object | Checkpoint, số bản ghi thực tế và giới hạn đã gặp. |
| `research/environment_inventory.json` | object | Snapshot file có sẵn trước tác vụ và công cụ ban đầu; không trộn nguồn gốc với đầu ra mới. |
| `reports/validation.json` | object | Kết quả kiểm tra kỹ thuật, số đếm và danh sách lỗi/cảnh báo. |

## Hồ sơ trang và dự án

`page_info` gồm `page_id`, `page_url`, `project_name`, `verification_status`, `source_status`, `collected_at`, `research_notes`. Các trường metadata xác minh được có thể bổ sung cùng nguồn đối chiếu. Tên và URL do người dùng cung cấp ban đầu được đánh dấu `user_provided_seed`, chưa tự coi là nội dung trang đã xác minh.

`project_info` gồm `project_id`, `name`, `name_meaning`, `founded_at`, `origin_story`, `mission`, `vision`, `objectives`, `core_values`, `partners`, `source_urls`, `verification_status`. Các mảng danh sách rỗng và trường `null` giữ nguyên khi chưa có nguồn. Không đưa số liệu của dự án trùng tên nhưng khác Facebook ID vào đây.

## Bài đăng

| Trường | Kiểu / ý nghĩa |
|---|---|
| `post_id` | string; ID nội bộ `post_` + 24 ký tự đầu hash của định danh ổn định. Ưu tiên Facebook ID, rồi URL, rồi thông tin gốc đủ nhận diện. |
| `facebook_post_id` | string hoặc null; không suy ra từ timestamp hay thứ tự xuất hiện. |
| `post_url` | string hoặc null trong export chưa đủ nguồn; URL trực tiếp. Validator báo thiếu khi chưa có URL để tra cứu. |
| `published_at` | ISO 8601 hoặc null; thời gian đăng bài, không mặc định là ngày sự kiện. |
| `caption_original` | string hoặc null; nguyên văn nội dung nguồn, giữ Unicode, emoji và xuống dòng. |
| `caption_clean` | string hoặc null; bản chuẩn hóa khoảng trắng phục vụ tìm kiếm, không thay thế nguyên bản. |
| `caption_completeness` | `complete`, `partial`, `unknown`; độ đầy đủ của nguyên văn thu được. |
| `hashtags`, `keywords` | array of strings; hashtag trích từ caption và từ khóa tra cứu. |
| `post_type` | string; `unknown` nếu chưa phân loại. |
| `season_ids`, `program_ids`, `journey_ids` | array of IDs; có thể liên quan nhiều mùa/hoạt động. |
| `photo_ids`, `video_ids` | array of IDs; liên kết tới media thật hoặc hồ sơ media nguồn. |
| `location_mentions` | array; tên địa điểm xuất hiện trong nguồn, không phải tọa độ đã xác minh. |
| `summary`, `historical_significance` | string hoặc null; tóm tắt/ý nghĩa biên tập có căn cứ. |
| `importance_score` | number hoặc null; không tự gán khi chưa đánh giá giá trị tư liệu. |
| `source_status` | Tình trạng nguồn; importer dùng `imported_export` cho dữ liệu export. |
| `verification_status` | `verified`, `inferred`, `unknown`; importer mặc định `unknown`. |
| `collected_at` | timestamp có offset; thời điểm nhập/thu thập, không phải thời gian sự kiện. |
| `provenance` | object; lưu nguồn nguyên bản, vị trí trích và hash. |

`provenance` của importer gồm `method`, `adapter`, `source_file`, `json_pointer`, `source_sha256`, `caption_field`, `input_basename`. `source_file` trỏ tới export lưu nguyên byte trong `data/raw/imports/`. `json_pointer` định vị bản ghi trong tài liệu; validator cũng đọc được dạng `entry/N` từ phiên bản cũ. `caption_field` có thể là `caption_original`, `post`, `message`, hoặc `data[*].post` khi caption ghép từ các đoạn `post` theo thứ tự nguồn. Caption từ nhiều đoạn được nối bằng ký tự xuống dòng; đây là phép trích có ghi rõ, không phải viết lại.

Adapter nhận mảng trực tiếp, object `posts`, hoặc export Facebook có `your_posts_v2`/`posts_v2`. Metadata như `title` hay caption từ kết quả tìm kiếm không được tự nhập thành nguyên văn bài Facebook. Chỉ đánh dấu `complete` khi có căn cứ từ nguồn đầy đủ; trạng thái này không tự chứng minh Facebook không cắt mất nội dung trước khi xuất.

Khi nhập lại, hợp nhất liên kết và giữ nội dung đã xác minh. Nếu caption nguồn mới khác caption đang lưu, importer giữ bản cũ và ghi `research/import_conflicts.json`; cần đối chiếu trước khi sửa.

## Ảnh và chỉ mục media

| Trường | Kiểu / ý nghĩa |
|---|---|
| `photo_id` | `photo_<24 ký tự đầu sha256>`; một ID cho cùng nội dung byte. |
| `local_path` | string hoặc null; ảnh thật tại `assets/originals/images/<sha256>.<ext>`. |
| `sha256`, `file_size` | Hash toàn file và kích thước byte thực tế. |
| `width`, `height`, `format` | Kích thước pixel và định dạng đọc từ file; không suy từ tên. |
| `source_url`, `source_urls` | URL media gốc và toàn bộ nguồn liên quan đã biết; null/[] nếu chỉ có file local. |
| `source_post_url`, `source_post_urls` | Bài đăng nguồn; mảng bảo toàn quan hệ nhiều bài cùng ảnh. |
| `facebook_photo_ids` | ID ảnh trên Facebook nếu trích được; cùng ID có thể có nhiều bản kích thước khác nhau. |
| `variant_group_id` | Khóa nhóm các file cùng một ID ảnh Facebook, dạng `fbphoto_<ID>`. |
| `variant_role` | `preferred` cho file độ phân giải tốt nhất hiện có; `alternate` cho bản kích thước khác vẫn giữ lại. |
| `preferred_photo_id` | Với bản `alternate`, trỏ tới `photo_id` của bản ưu tiên trong cùng nhóm. |
| `post_ids`, `source_post_ids` | ID bài đã lưu; không được trỏ tới ID chưa có trong `posts.json`. |
| `season_ids`, `program_ids`, `journey_ids` | Liên kết có căn cứ; không phân mùa chỉ bằng hình hoặc ngày đăng. |
| `published_at` | Ngày đăng nguồn nếu xác định được. |
| `downloaded_at` | Thời điểm tải từ nguồn từ xa; để null khi ảnh có sẵn trên máy. |
| `imported_at` | Thời điểm nhập file local. |
| `download_status` | `local_imported` cho file nhập từ workspace; `downloaded` cho file tải từ xa; trạng thái lỗi phải được giữ rõ. |
| `local_sources` | Các đường dẫn file gốc trên máy trong workspace, giữ dấu vết trước khi chuẩn hóa tên. |
| `description`, `category` | Nội dung mô tả và phân loại; null nếu chưa xem/đối chiếu. |
| `importance_score` | number hoặc null; đánh giá tư liệu, không đồng nghĩa đẹp hoặc được duyệt. |
| `rights_status` | `unknown`, `permission_confirmed`, `owned`, `licensed`, `restricted`. |
| `rights_evidence` | Bằng chứng quyền sử dụng; bắt buộc với các trạng thái khẳng định quyền khi dùng importer. |
| `privacy_review_required` | boolean; mặc định true, phải xem xét trước khi đưa lên website. |
| `publication_status` | `not_reviewed` mặc định; tách biệt việc có file và quyền xuất bản. |
| `provenance` | Với file local: `method: local_original_import`, `input_basename`. |

`media_index` thêm `media_id` bằng `photo_id`/`video_id`, `media_type: photo` hoặc `video`, và metadata tương ứng. Validator kiểm tra ID này khớp bảng gốc. Hash giống nhau giúp giữ một bản vật lý và bảo toàn tất cả quan hệ nguồn; không xóa ảnh chụp gần giống nhau.

Số bản ghi/file ảnh, số ID ảnh Facebook riêng biệt, số ảnh nhập local và số ảnh tải Facebook là các số khác nhau. `research/media_variant_groups.json` liệt kê từng ID ảnh, toàn bộ `photo_ids` và bản ưu tiên. Liên kết ảnh trong hồ sơ mùa dùng bản ưu tiên để tránh đếm lại bản nhỏ và bản lớn; bản còn lại vẫn nằm trong kho gốc. Ảnh local không có `source_url` được giữ để nghiên cứu; không được gọi là ảnh đã tải từ Facebook.

## Video và album

Video dùng `video_id`, `source_url`, `published_at`, caption, `season_ids`, `program_ids`, mô tả, thumbnail khi được phép, thời lượng nếu biết, `download_status`, `rights_status`, `privacy_review_required`. Nếu không được phép tải, để `local_path: null`, lưu URL và trạng thái đúng thực tế. Khi có file local, phải thêm `sha256`, `file_size` và metadata kiểm tra được; không tạo file giả để thay video.

Album dùng `album_id`, URL/tên album gốc, mô tả, thời gian nếu có nguồn, `post_ids`, `photo_ids`, `video_ids`, `season_ids` và ghi chú xác minh. Schema chi tiết được bổ sung khi có album thật; mảng trống hiện tại không phải album mẫu.

## Mùa

| Trường | Kiểu / ý nghĩa |
|---|---|
| `season_id` | string ổn định, không đổi theo vị trí trong mảng. |
| `season_number` | positive integer hoặc null; không dùng chuỗi `unknown`, không suy từ năm. |
| `official_name`, `theme`, `slogan` | string hoặc null; phân biệt tên nguyên gốc và tiêu đề biên tập nếu cần bổ sung. |
| `start_date`, `end_date` | ISO 8601 hoặc null theo độ chính xác nguồn; không lấy ngày bài giới thiệu thay ngày mùa. |
| `description` | string hoặc null; mô tả có nguồn, giữ các giới hạn chưa biết. |
| `objectives`, `locations` | array; thông tin có bằng chứng liên quan trực tiếp mùa. |
| `program_ids`, `journey_ids` | Chương trình và chuyến đi thuộc mùa đã đối chiếu. |
| `post_ids`, `photo_ids`, `video_ids`, `milestone_ids` | Liên kết đến thực thể có thật trong kho. |
| `source_urls` | array of URLs; mùa `verified` phải có nguồn trực tiếp chứng minh số/tên mùa. |
| `verification_status`, `research_notes` | Trạng thái và các điểm cần làm rõ. |
| `evidence_ids` nếu dùng | Liên kết khẳng định chi tiết trong `research/evidence_map.json`. |

Hồ sơ từng mùa nằm trong `data/seasons/<season_id>/`: `season_info.json`, `posts.json`, `programs.json`, `journeys.json`, `timeline.json`, `media_manifest.json`, `season_story.md`, `sources.md`. Dữ liệu này phải khớp các bảng tổng hợp, không chứa ID hư hoặc sự kiện giả định.

## Chương trình, chuyến đi, timeline và nội dung biên tập

Các bản ghi chương trình/chuyến đi sử dụng lần lượt `program_id`/`journey_id`, tên, mô tả, mục tiêu khi có, thời gian, địa điểm, nguồn, `verification_status` và các mảng quan hệ. Thực thể có thể chưa biết mùa; giữ `season_ids: []`, không tạo mùa tạm giả. Không biến ngày đăng báo hoặc ngày bài hồi tưởng thành ngày diễn ra hoạt động.

Timeline dùng `event_id`, ngày thực sự diễn ra (`event_date`, hoặc `date` khi adapter dùng trường đó), tiêu đề/mô tả, các ID bài/chương trình/chuyến đi/mùa/media và `source_urls`. Validator hỗ trợ thêm `start_date`, `event_start` cho ngày bắt đầu; `end_date`, `event_end` cho ngày kết thúc. Chỉ các sự kiện đã biết ngày mới có thể được xếp thứ tự chắc chắn; ngày chưa biết được cảnh báo. Không xếp lại sự kiện dựa trên `published_at` khi đó là bài hồi tưởng.

`milestones`, `stories`, `featured_content` là lớp biên tập. Mỗi khẳng định quan trọng phải trỏ tới nguồn trực tiếp hoặc `evidence_ids` có thể tra cứu. Nội dung gợi ý cho `homepage_hero`, `season_cover`, `timeline_image` hoặc vị trí khác không cấp quyền xuất bản ảnh. Chưa có bằng chứng thì giữ mảng trống, không viết câu chuyện lấp chỗ trống.

## Độ chính xác thời gian

Ngày giờ chính xác dùng ISO 8601 có múi giờ, ví dụ offset `+07:00` cho giờ Việt Nam/Thái Lan hoặc `Z` cho UTC. Ngày sự kiện đầy đủ dùng `YYYY-MM-DD`. Chỉ biết tháng hoặc năm thì giữ `YYYY-MM`/`YYYY`, ghi rõ độ chính xác ở metadata hoặc ghi chú; không tự thêm `-01`. Giá trị hoàn toàn chưa biết là null.

`published_at` là thời điểm xuất bản; `collected_at`, `downloaded_at`, `imported_at` là thời điểm tác nghiệp. `start_date`/`end_date` hoặc `event_date` mới mô tả hoạt động thực tế khi nguồn chứng minh. Validator so sánh thứ tự chỉ ở độ chính xác mà cả hai mốc cùng biết, không bịa ngày còn thiếu.

## Hàng đợi và checkpoint

Mỗi URL phát hiện gồm `discovery_id`, `url`, `kind`, `facebook_post_id`, `post_id`, `discovered_at`, `source_urls`, `pipeline`, `errors`. `kind` từ parser hiện hỗ trợ `post`, `photo`, `video`, `album`, `page_or_unknown`; liên kết chưa phân loại không bị bỏ.

`pipeline` chứa các boolean độc lập `discovered`, `content_extracted`, `media_downloaded`, `season_classified`, `verified`. `media_downloaded: false` không được đổi thành true chỉ vì đã có URL ảnh. Một URL profile được phát hiện không tương đương một bài đăng đã thu thập.

`collection_progress` ghi `updated_at`, `last_operation`, `last_operation_details`, `counts` theo file, `pipeline_counts`, `seasons_verified`, `historical_coverage: unknown`, `empty_arrays_are_collected_data: false`. Các giới hạn truy cập/ghi chú bổ sung được giữ lại khi cập nhật. Checkpoint hỗ trợ chạy tiếp, không phải chứng nhận hoàn tất lịch sử.

## Kiểm tra chất lượng và giới hạn

Chạy `python3 scripts/validation/validate_archive.py` sau khi cập nhật dữ liệu. Lệnh xuất `reports/validation.json` và `reports/DATA_QUALITY_REPORT.md`, trả exit code 1 khi có lỗi kỹ thuật. `integrity_status` nhận `failed`, `passed_with_warnings`, `passed`; cả hai trạng thái pass chỉ nói về dữ liệu đã có.

Validator kiểm tra JSON, container, ID trùng, tham chiếu, ngày/chronology, trạng thái caption, nguồn mùa, hash/size/dimensions/decode media, quyền/riêng tư và hash file ban đầu. Khi có provenance export được hỗ trợ, caption được so sánh nguyên văn với nguồn lưu trên đĩa. Có URL nguồn không đủ để validator tự chứng minh nội dung; các mối liên kết lịch sử vẫn phải được đọc và đối chiếu.

`counts` phân biệt `posts_archived`, `photo_metadata_records`, `photos_with_local_file`, `photos_imported_from_workspace`, `photos_downloaded_from_remote`, số mùa xác minh, chương trình, chuyến đi và timeline. `total_facebook_posts` và `facebook_history_completion_percent` để null khi không biết tổng thật. Cảnh báo quyền chưa rõ, bài/media chưa có mùa hoặc chưa nối được bài nguồn được giữ công khai trong báo cáo để xử lý tiếp.

Thư mục `.git`, `.agents`, `.aws`, `.codex` không phải nguồn tư liệu; không đọc secret hay thêm nội dung của chúng vào kho. Không nhận dạng khuôn mặt, không đoán danh tính hay đặc điểm nhạy cảm, không công bố thông tin riêng tư của trẻ em/người thụ hưởng từ tư liệu nghiên cứu.
