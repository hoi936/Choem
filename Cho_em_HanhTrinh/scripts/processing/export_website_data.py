#!/usr/bin/env python3
"""Generate website/data/archive_bundle.js with full Unicode normalization,
natural Vietnamese sentence-case typography, smart quote formatting,
curated Season 5 HD field-action stills, distinct photo captions, and post categorization."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"D:\CHO_EM\Cho_em_HanhTrinh")

# Curated, visually distinct, face-forward field-action hero photos for each season
CURATED_SEASON_HERO_PHOTOS = {
    "season_01": "assets/originals/images/e8b97e275521d0d231ce22f6fae7df84db72860e9b1b00698cb034c73e06101f.jpg",
    "season_02": "assets/originals/images/6d6788f02cb7212fb85b92ab8f76f946f8ca2764426006044b07993e91e19812.jpg",
    "season_03": "assets/originals/images/d9445fe053b236a7c0572b736d7303168838a5eeb5f553dee04675910a22b4e9.jpg",
    "season_04": "assets/originals/images/31cf728b3219196b2a18f64f00310328678521cfbde39cd6879d8e00e9d5df00.jpg",
    "season_05": "assets/originals/images/s5_tan_thanh_03.jpg",
    "season_06": "assets/originals/images/1faaae04a9a2a1a523c483beece6c2d257bcdb477d4a9d07be6ab027b42b0ee2.jpg",
    "season_07": "assets/originals/images/7ba9098fdc4881a066d0c4ebfe1cbb6985f3af04a5bb00aadb1611458f465752.jpg",
}

# Curated 4-photo highlight strip per season for the Season Explorer
CURATED_SEASON_HIGHLIGHTS = {
    "season_01": [
        "assets/originals/images/e8b97e275521d0d231ce22f6fae7df84db72860e9b1b00698cb034c73e06101f.jpg",
        "assets/originals/images/9844d396e4a5c67492bea7d86eb63dafc975d0c616c8d2f7b2d931c11628a910.jpg",
        "assets/originals/images/f8d9667be7787ba5fd5e7199df4fd2f5fdbc5e884381f9eda5f7fae4d0082035.jpg",
        "assets/originals/images/76d8bf49b32fea0c24f0b442c614871c687ede1aa38a10d13108a971e44040b6.jpg",
    ],
    "season_02": [
        "assets/originals/images/6d6788f02cb7212fb85b92ab8f76f946f8ca2764426006044b07993e91e19812.jpg",
        "assets/originals/images/9e7760b490f69ced5db5e3ba5502cd91b34d1659ec65f592a77ecb5725576c06.jpg",
        "assets/originals/images/ab2d62dddc3baa60a2fe4d85c56d317be86737b4767699a57b30bf9bffcde3b3.jpg",
        "assets/originals/images/b0ce5ca5b4e27fa095f834802c5e15deea97a0c34ca4642717f1a6786736ad3b.jpg",
    ],
    "season_03": [
        "assets/originals/images/d9445fe053b236a7c0572b736d7303168838a5eeb5f553dee04675910a22b4e9.jpg",
        "assets/originals/images/9e0e3c10cbe01ac5805ade5c52cc6554bca269eee8a9a8e85e369ceb3309f54d.jpg",
        "assets/originals/images/50dd5ef4d1ab731d82a29432f64f654b00367d72092da74cc7682cee7c2b979b.jpg",
        "assets/originals/images/e460e10efff29c165d6f9ad19b8c92c6c48cfaef857dca28c93d774e6041d377.jpg",
    ],
    "season_04": [
        "assets/originals/images/31cf728b3219196b2a18f64f00310328678521cfbde39cd6879d8e00e9d5df00.jpg",
        "assets/originals/images/8d9ea905ef8ec3d79c0f7cf9930aa3ff1ab8bd94dc04e9c6e21c25824b20d5c5.jpg",
        "assets/originals/images/bb5863376dfd7b3759e318b8b03ba0084425329187829969202f82e1985e2517.jpg",
        "assets/originals/images/9665314bc5ce3d57a93ba610a407367b73251b4c6575b0e7954727b9dfa11d78.jpg",
    ],
    "season_05": [
        "assets/originals/images/s5_tan_thanh_03.jpg",
        "assets/originals/images/s5_tan_thanh_07.jpg",
        "assets/originals/images/s5_tan_thanh_09.jpg",
        "assets/originals/images/1a8a1294e364cbccd2d08ed716c2fc79db67a0804fe1e09dd8e596caf8d5d358.jpg",
    ],
    "season_06": [
        "assets/originals/images/1faaae04a9a2a1a523c483beece6c2d257bcdb477d4a9d07be6ab027b42b0ee2.jpg",
        "assets/originals/images/7dd6034b3e3ca15f668eaf390e17b38cdbf50bddff9ba58f3af7edbefdccd771.jpg",
        "assets/originals/images/36cd57ce1b4a925957591608ab67568141343d344f321c13bd3999e045687e6d.jpg",
        "assets/originals/images/0ce8d4ef4a85b62b05fe4c3c80e5661800c2ce4e519eb8f218b01c5cfa523c74.jpg",
    ],
    "season_07": [
        "assets/originals/images/7ba9098fdc4881a066d0c4ebfe1cbb6985f3af04a5bb00aadb1611458f465752.jpg",
        "assets/originals/images/2b0a5ffc21321e27a4915c3a564b50a2e3504c0ab5c68d8181afedab99de0b35.jpg",
        "assets/originals/images/e80945c3c6ef5835cb17adbbe79120cc1ddafa461cbad90ec3d29aa388ad5f51.jpg",
        "assets/originals/images/4888c205538e675560da38793e0363f927e6e15d7cb7f7f07b30d872997bc580.jpg",
    ],
}

# 10 HD documentary stills extracted from Season 5 Recap Film (11/08/2025 at TH&THCS Tân Thành)
SEASON_05_EXTRACTED_PHOTOS = [
    {
        "photo_id": "photo_s5_tan_thanh_03",
        "local_path": "assets/originals/images/s5_tan_thanh_03.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Tình nguyện viên CHO EM ân cần cài bảng tên và trò chuyện cùng học sinh Tân Thành",
        "description": "Khoảnh khắc mở đầu chương trình “An toàn cho em” ngày 11/08/2025 tại Trường TH&THCS Tân Thành (Hướng Hóa): các anh chị áo xanh tận tay ghi và cài từng tấm thẻ tên cho các em học sinh khối 4, 5.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_07",
        "local_path": "assets/originals/images/s5_tan_thanh_07.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Tiết học thực hành kỹ năng sơ cứu trực quan tại lớp học Trường TH&THCS Tân Thành",
        "description": "Các thành viên Ban Nội dung trực tiếp hướng dẫn các em học sinh cách nhận biết và xử lý vết thương, băng bó sơ cứu cơ bản bằng bộ dụng cụ y tế chuẩn Bộ Y Tế.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_09",
        "local_path": "assets/originals/images/s5_tan_thanh_09.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Trao tận tay hơn 100 suất quà khuyến học và 100 đôi giày mới cho các em nhỏ Tân Thành",
        "description": "Niềm vui rạng rỡ của các em học sinh khối 4, 5 Trường TH&THCS Tân Thành khi lên sân khấu nhận những phần quà học tập và 100 đôi giày mới trước thềm năm học.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_01",
        "local_path": "assets/originals/images/s5_tan_thanh_01.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Các em học sinh Trường TH&THCS Tân Thành hào hứng vỗ tay đón đoàn tình nguyện",
        "description": "Hội trường Trường TH&THCS Tân Thành rộn ràng tiếng vỗ tay và ánh mắt háo hức của các em nhỏ miền núi Hướng Hóa trong buổi sáng 11/08/2025.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_06",
        "local_path": "assets/originals/images/s5_tan_thanh_06.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Sân khấu chính chương trình “An toàn cho em” cùng hơn 100 phần quà đã sẵn sàng",
        "description": "Không gian hội trường Trường TH&THCS Tân Thành với hơn 100 phần quà khuyến học và 04 bộ sơ cấp cứu loại A chuẩn Bộ Y Tế chuẩn bị trao gửi.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_05",
        "local_path": "assets/originals/images/s5_tan_thanh_05.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Hướng dẫn quy tắc 3C (Check – Call – Care) khi gặp tình huống khẩn cấp",
        "description": "Bài giảng minh họa sinh động giúp các em nhỏ vùng cao dễ dàng ghi nhớ 3 bước kiểm tra an toàn, gọi người trợ giúp và chăm sóc ban đầu.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_08",
        "local_path": "assets/originals/images/s5_tan_thanh_08.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Chuyên đề xử lý an toàn khi bị côn trùng đốt nơi miền núi",
        "description": "Những kiến thức thực tế, gần gũi với đời sống hàng ngày của học sinh miền núi được các anh chị CHO EM truyền tải dễ hiểu tại lớp học.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_02",
        "local_path": "assets/originals/images/s5_tan_thanh_02.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Các tiết mục vận động khởi động sôi nổi đầu giờ cùng anh chị áo xanh",
        "description": "Xóa tan sự bỡ ngỡ ban đầu, các em học sinh khối 4, 5 cùng đứng dậy múa hát và tham gia trò chơi khởi động với Ban Tổ chức.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_04",
        "local_path": "assets/originals/images/s5_tan_thanh_04.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Các em nhỏ chăm chú theo dõi phim hoạt hình tình huống sơ cứu",
        "description": "Thông qua các đoạn phim hoạt hình trực quan, các em học sinh hào hứng giơ tay trả lời câu hỏi về cách tự bảo vệ bản thân trước tai nạn thương tích.",
    },
    {
        "photo_id": "photo_s5_tan_thanh_10",
        "local_path": "assets/originals/images/s5_tan_thanh_10.jpg",
        "width": 1280,
        "height": 720,
        "published_at": "2025-08-18T13:39:36+00:00",
        "title_clean": "Ống kính truyền thông lưu giữ từng nụ cười tại điểm trường Tân Thành",
        "description": "Đội ngũ Truyền thông CHO EM mùa 5 ghi lại trọn vẹn những ánh mắt lấp lánh và kỷ niệm đẹp tại Trường TH&THCS Tân Thành.",
    },
]

# Natural Vietnamese typography overrides
SEASON_TYPOGRAPHY_OVERRIDES = {
    "season_01": {
        "official_name": "CHO EM mùa 1 — “Sân chơi cho em”",
        "theme": "Xây dựng sân chơi tái chế cho trẻ em vùng cao",
        "slogan": "“Sân chơi cho em, cho em niềm vui, gieo mầm ước mơ”",
        "story_title": "“Người nhỏ làm việc nhỏ” — Hành trình 80km vượt đèo lên bản Ho Le & Tà Rùng",
    },
    "season_02": {
        "official_name": "CHO EM mùa 2 — “Răng xinh cho em”",
        "theme": "Chăm sóc sức khỏe răng miệng học đường",
        "slogan": "“Vì những nụ cười trẻ thơ — Góp phần nhỏ vì một tương lai tươi sáng hơn của trẻ em Quảng Trị”",
        "story_title": "“Hai ba bàn chải nhỏ” — Giữ trọn nụ cười xinh nơi vùng biển cát Triệu Vân",
    },
    "season_03": {
        "official_name": "CHO EM mùa 3 — “Sân chơi cho em” (mùa 3)",
        "theme": "Tiếp tục sứ mệnh — Nối tiếp hành trình xây sân chơi vùng cao",
        "slogan": "“Sân chơi cho em, cho em niềm vui, gieo mầm ước mơ”",
        "story_title": "Nắng hè Đông Hà & niềm vui nơi điểm trường Chênh Vênh, Hướng Choa",
    },
    "season_04": {
        "official_name": "CHO EM mùa 4 — “Phao xinh cho em”",
        "theme": "Tuyên truyền phòng chống đuối nước & sẻ chia hơi ấm mùa xuân",
        "slogan": "“Tết đoàn viên năm nay, cùng CHO EM chia sẻ yêu thương”",
        "story_title": "Hành trang tuổi 18 & mùa xuân nơi ngôi trường gần biển Triệu Lăng",
    },
    "season_05": {
        "official_name": "CHO EM mùa 5 — “An toàn cho em”",
        "theme": "Giáo dục kỹ năng sơ cứu cơ bản & tự bảo vệ trước tai nạn thương tích",
        "slogan": "“Trang bị kỹ năng sống an toàn — Lan tỏa yêu thương đến trẻ em vùng cao”",
        "story_title": "“Sự sẻ chia là liều thuốc quý giá nhất” — Chuyến xe mùa 5 đến với Tân Thành",
    },
    "season_06": {
        "official_name": "CHO EM mùa 6 — “An toàn cho em 2”",
        "theme": "Trang bị “tấm lá chắn kỹ năng” sơ cứu cho trẻ em vùng sâu Vĩnh Ô",
        "slogan": "“An toàn cho em — Gửi trọn yêu thương”",
        "story_title": "Vượt đèo lên Vĩnh Ô — Mang “tấm lá chắn kỹ năng” giữa mùa đông ấm áp",
    },
    "season_07": {
        "official_name": "CHO EM mùa 7 — “Hành trang cho em”",
        "theme": "Phòng chống tai nạn đuối nước & trao tủ sách tri thức vùng cao",
        "slogan": "“Cùng Hành trang cho em — Thay màu áo mới, bảo vệ nụ cười thơ”",
        "story_title": "“Hành trang cho em” — Những chiếc áo phao cam & tủ sách tri thức giữa núi rừng Tà Long",
    },
}

TIMELINE_TITLE_OVERRIDES = {
    "event_project_founded_20230717": (
        "Thành lập trang chính thức dự án thiện nguyện “CHO EM”",
        "Trang Facebook chính thức dự án “CHO EM” được khởi tạo tại Đông Hà, Quảng Trị, mở đầu hành trình vì trẻ em vùng cao.",
    ),
    "event_season_01_kickoff": (
        "Khởi động CHO EM mùa 1 — “Sân chơi cho em”",
        "Mở đầu hành trình CHO EM mùa 1 — “Sân chơi cho em” với chủ đề xây dựng sân chơi tái chế cho trẻ em vùng cao.",
    ),
    "event_season_01_main_program": (
        "Sự kiện chính mùa 1: Khánh thành 02 sân chơi “Sân chơi cho em” tại bản Ho Le & Tà Rùng",
        None,
    ),
    "event_season_02_kickoff": (
        "Khởi động CHO EM mùa 2 — “Răng xinh cho em”",
        "Mở đầu hành trình CHO EM mùa 2 — “Răng xinh cho em” với chủ đề chăm sóc sức khỏe răng miệng học đường.",
    ),
    "event_season_02_main_program": (
        "Sự kiện chính mùa 2: Chương trình “Răng xinh cho em” tại xã Triệu Vân",
        None,
    ),
    "event_season_03_kickoff": (
        "Khởi động CHO EM mùa 3 — “Sân chơi cho em” (mùa 3)",
        "Mở đầu hành trình CHO EM mùa 3 — “Sân chơi cho em” (mùa 3), tiếp nối sứ mệnh xây dựng sân chơi cho trẻ em vùng cao Hướng Hóa.",
    ),
    "event_season_03_main_program": (
        "Sự kiện chính mùa 3: Khánh thành sân chơi “Sân chơi cho em” tại Chênh Vênh & Hướng Choa",
        None,
    ),
    "event_season_04_kickoff": (
        "Khởi động CHO EM mùa 4 — “Phao xinh cho em”",
        "Mở đầu hành trình CHO EM mùa 4 — “Phao xinh cho em” với chủ đề tuyên truyền phòng chống đuối nước và sẻ chia hơi ấm mùa xuân.",
    ),
    "event_season_04_main_program": (
        "Sự kiện chính mùa 4: Ngày hội kỹ năng “Phao xinh cho em” tại xã Triệu Vân",
        None,
    ),
    "event_season_05_kickoff": (
        "Khởi động CHO EM mùa 5 — “An toàn cho em”",
        "Mở đầu hành trình CHO EM mùa 5 — “An toàn cho em” với chủ đề giáo dục kỹ năng sơ cứu cơ bản và tự bảo vệ trước tai nạn thương tích.",
    ),
    "event_season_05_main_program": (
        "Sự kiện chính mùa 5: Chuyên đề “An toàn cho em” tại xã Tân Thành",
        None,
    ),
    "event_season_06_kickoff": (
        "Khởi động CHO EM mùa 6 — “An toàn cho em 2”",
        "Mở đầu hành trình CHO EM mùa 6 — “An toàn cho em 2”, mang tấm lá chắn kỹ năng sơ cứu đến với trẻ em vùng sâu Vĩnh Ô.",
    ),
    "event_season_06_main_program": (
        "Sự kiện chính mùa 6: Chương trình “An toàn cho em 2” tại xã Vĩnh Ô",
        None,
    ),
    "event_season_07_kickoff": (
        "Khởi động CHO EM mùa 7 — “Hành trang cho em”",
        "Mở đầu hành trình CHO EM mùa 7 — “Hành trang cho em” với chủ đề phòng chống tai nạn đuối nước và trao tủ sách tri thức vùng cao.",
    ),
    "event_season_07_main_program": (
        "Sự kiện chính mùa 7: Chương trình “Hành trang cho em” tại điểm trường Tà Long",
        None,
    ),
}

TITLE_CASE_PHRASE_FIXES = [
    ("Sân Chơi Cho Em (Mùa 3)", "“Sân chơi cho em” (mùa 3)"),
    ("Sân Chơi Cho Em (Mùa 1)", "“Sân chơi cho em” (mùa 1)"),
    ("Sân Chơi Cho Em", "“Sân chơi cho em”"),
    ("Răng Xinh Cho Em", "“Răng xinh cho em”"),
    ("Phao Xinh Cho Em", "“Phao xinh cho em”"),
    ("An Toàn Cho Em 2", "“An toàn cho em 2”"),
    ("An Toàn Cho Em", "“An toàn cho em”"),
    ("Hành Trang Cho Em", "“Hành trang cho em”"),
    ("CHO EM Mùa ", "CHO EM mùa "),
]

# Proper nouns & acronyms to preserve when converting ALL-CAPS titles to Vietnamese sentence case
PROPER_NOUN_REPLACEMENTS = [
    (r"\bcho em\b", "CHO EM"),
    (r"\bbtc\b", "BTC"),
    (r"\bthpt\b", "THPT"),
    (r"\bth&thcs\b", "TH&THCS"),
    (r"\bthcs\b", "THCS"),
    (r"\bptdtbt\b", "PTDTBT"),
    (r"\bth\s+vĩnh\s+ô\b", "TH Vĩnh Ô"),
    (r"\bth\s+tà\s+long\b", "TH Tà Long"),
    (r"\blê\s+quý\s+đôn\b", "Lê Quý Đôn"),
    (r"\bquảng\s+trị\b", "Quảng Trị"),
    (r"\bđông\s+hà\b", "Đông Hà"),
    (r"\bhướng\s+hóa\b", "Hướng Hóa"),
    (r"\bhướng\s+phùng\b", "Hướng Phùng"),
    (r"\bhướng\s+choa\b", "Hướng Choa"),
    (r"\bchênh\s+vênh\b", "Chênh Vênh"),
    (r"\bho\s+le\b", "Ho Le"),
    (r"\btà\s+rùng\b", "Tà Rùng"),
    (r"\bxã\s+húc\b", "xã Húc"),
    (r"\btriệu\s+vân\b", "Triệu Vân"),
    (r"\btriệu\s+phong\b", "Triệu Phong"),
    (r"\btriệu\s+lăng\b", "Triệu Lăng"),
    (r"\btân\s+thành\b", "Tân Thành"),
    (r"\bvĩnh\s+ô\b", "Vĩnh Ô"),
    (r"\bvĩnh\s+linh\b", "Vĩnh Linh"),
    (r"\btà\s+long\b", "Tà Long"),
    (r"\bpa\s+hy\b", "Pa Hy"),
    (r"\bđakrông\b", "Đakrông"),
    (r"\blê\s+na\b", "Lê Na"),
    (r"\bcolena\b", "Colena"),
    (r"\bmiss\s+kha\b", "Miss Kha"),
    (r"\blê\s+tú\s+linh\s+kha\b", "Lê Tú Linh Kha"),
    (r"\bthầy\s+thông\b", "Thầy Thông"),
    (r"\bthu\s+hồng\s+lê\b", "Thu Hồng Lê"),
    (r"\bhạnh\s+nguyên\b", "Hạnh Nguyên"),
    (r"\blê\s+thị\s+vân\b", "Lê Thị Vân"),
    (r"\blê\s+minh\s+tuấn\b", "Lê Minh Tuấn"),
    (r"\bnguyễn\s+thị\s+thanh\s+huyền\b", "Nguyễn Thị Thanh Huyền"),
    (r"\btrần\s+mai\s+hương\s+nguyên\b", "Trần Mai Hương Nguyên"),
    (r"\bnguyễn\s+thị\s+kiều\s+trinh\b", "Nguyễn Thị Kiều Trinh"),
    (r"\btrần\s+quang\s+khang\b", "Trần Quang Khang"),
    (r"\bnguyễn\s+việt\s+đức\b", "Nguyễn Việt Đức"),
    (r"\blê\s+khánh\s+linh\b", "Lê Khánh Linh"),
    (r"\bsang\s+hiếu\b", "Sang Hiếu"),
    (r"\bbảo\s+châu\b", "Bảo Châu"),
    (r"\bgreen\s+center\b", "Green Center"),
    (r"\bgreen\s+centre\b", "Green Centre"),
    (r"\bsky\s+garden\b", "Sky Garden"),
    (r"\bjoy\s+school\b", "Joy School"),
    (r"\bmây\s+mart\b", "Mây Mart"),
    (r"\bthe\s+moment\s+cafe\s*&\s*food\b", "The Moment Cafe & Food"),
    (r"\bgạo\s+coffee\b", "Gạo Coffee"),
    (r"\bgé\s+nhà\b", "Gé Nhà"),
    (r"\bdimori\s+coffee\b", "Dimori Coffee"),
    (r"\bchút\s+chíu\b", "Chút Chíu"),
    (r"\bhạt\s+màu\s+nắng\b", "Hạt Màu Nắng"),
    (r"\bapical\s+bud\b", "Apical Bud"),
    (r"\bqna\b", "Q&A"),
    (r"\brecap\b", "Tổng kết"),
    (r"\bpre\s*-\s*order\b", "Pre-order"),
    (r"\bworkshop\b", "Workshop"),
    (r"\bminigame\b", "Minigame"),
]

# Bespoke, exact titles for featured and highlight photos
BESPOKE_PHOTO_TITLES = {
    "assets/originals/images/e8b97e275521d0d231ce22f6fae7df84db72860e9b1b00698cb034c73e06101f.jpg": "Các em nhỏ bản Ho Le (xã Húc) thích thú vui đùa trên xích đu và bập bênh lốp xe tái chế",
    "assets/originals/images/6d6788f02cb7212fb85b92ab8f76f946f8ca2764426006044b07993e91e19812.jpg": "Học sinh Trường TH&THCS Triệu Vân chăm chú theo dõi vở kịch “Răng xinh cho em”",
    "assets/originals/images/d9445fe053b236a7c0572b736d7303168838a5eeb5f553dee04675910a22b4e9.jpg": "Lễ khánh thành và bàn giao sân chơi tái chế tại điểm trường Chênh Vênh (Hướng Phùng)",
    "assets/originals/images/31cf728b3219196b2a18f64f00310328678521cfbde39cd6879d8e00e9d5df00.jpg": "Ngày hội tuyên truyền kỹ năng phòng chống đuối nước “Phao xinh cho em” tại Triệu Vân",
    "assets/originals/images/1faaae04a9a2a1a523c483beece6c2d257bcdb477d4a9d07be6ab027b42b0ee2.jpg": "Nụ cười ấm áp của học sinh Trường PTDTBT Tiểu học Vĩnh Ô trong chiếc áo khoác mùa đông",
    "assets/originals/images/7dd6034b3e3ca15f668eaf390e17b38cdbf50bddff9ba58f3af7edbefdccd771.jpg": "Trao tặng 67 suất quà Tết cho học sinh vượt khó tại Trường PTDTBT Tiểu học Vĩnh Ô",
    "assets/originals/images/36cd57ce1b4a925957591608ab67568141343d344f321c13bd3999e045687e6d.jpg": "Niềm vui của các em nhỏ vùng sâu Vĩnh Ô khi đón nhận túi quà mùa xuân từ anh chị CHO EM",
    "assets/originals/images/0ce8d4ef4a85b62b05fe4c3c80e5661800c2ce4e519eb8f218b01c5cfa523c74.jpg": "Sân khấu chương trình “An toàn cho em 2” cùng những phần quà Tết tại xã Vĩnh Ô",
    "assets/originals/images/7ba9098fdc4881a066d0c4ebfe1cbb6985f3af04a5bb00aadb1611458f465752.jpg": "Nụ cười rạng rỡ của tình nguyện viên và học sinh Tiểu học Tà Long bên những chiếc áo phao mới",
    "assets/originals/images/2b0a5ffc21321e27a4915c3a564b50a2e3504c0ab5c68d8181afedab99de0b35.jpg": "Em nhỏ Trường Tiểu học Tà Long nâng niu chiếc áo phao cứu sinh trước thềm năm học mới",
    "assets/originals/images/e80945c3c6ef5835cb17adbbe79120cc1ddafa461cbad90ec3d29aa388ad5f51.jpg": "Nụ cười trong veo của học sinh điểm trường Pa Hy — Tiểu học Tà Long (Đakrông)",
    "assets/originals/images/4888c205538e675560da38793e0363f927e6e15d7cb7f7f07b30d872997bc580.jpg": "Trao bảng tượng trưng 02 “Tủ sách tri thức” (345 đầu sách) cho Trường Tiểu học Tà Long",
    "assets/originals/images/6ecca86af231ae5f30c18bb9c07ac7d09cb3c6b5854115f0034bde28a5d5e398.jpg": "Tập thể tình nguyện viên mùa 7 trước cổng Trường THPT Chuyên Lê Quý Đôn giờ xuất phát",
}

# Rich descriptive templates for multi-photo album sequences so cards never repeat identical titles
ALBUM_MOMENT_DESCRIPTIONS = {
    "season_01": [
        "Niềm vui của các em nhỏ bản Ho Le trên xích đu lốp xe mới",
        "Khoảnh khắc vui đùa trên cầu bập bênh gỗ tại điểm trường xã Húc",
        "Tình nguyện viên CHO EM cùng lắp đặt sân chơi tái chế giữa núi rừng Hướng Hóa",
        "Nụ cười hồn nhiên của trẻ thơ vùng cao trong ngày khánh thành sân chơi",
        "Trao tận tay những phần bánh kẹo và quần áo mới cho các em nhỏ xã Húc",
        "Sắc màu rực rỡ của những chiếc lốp xe tái chế do học sinh Đông Hà tự sơn vẽ",
    ],
    "season_02": [
        "Các em học sinh Trường TH&THCS Triệu Vân chăm chú theo dõi vở kịch “Răng xinh cho em”",
        "Nụ cười rạng rỡ của học sinh vùng biển bãi ngang trong tiết học chăm sóc răng miệng",
        "Tình nguyện viên hướng dẫn các em thực hành chải răng đúng cách theo từng bước",
        "Những cánh tay hào hứng giơ cao trả lời câu hỏi đố vui sức khỏe học đường",
        "Trao gửi những bộ bàn chải, kem đánh răng và phần quà Tết tại Triệu Vân",
        "Khoảnh khắc giao lưu ấm áp giữa anh chị áo xanh CHO EM và học sinh Triệu Phong",
    ],
    "season_03": [
        "Lễ khánh thành sân chơi tái chế tại điểm trường Chênh Vênh (Hướng Phùng)",
        "Các em nhỏ mầm non Hướng Choa háo hức trải nghiệm xích đu và ngựa gỗ mới",
        "Tình nguyện viên CHO EM mùa 3 vận chuyển từng thiết bị sân chơi vượt đèo lên bản",
        "Trao tặng vở tập tô, đồ chơi và bánh kẹo cho các em nhỏ xã Hướng Phùng",
        "Niềm hạnh phúc của cô và trò điểm trường Chênh Vênh bên khoảng sân chơi đầy nắng",
        "Tập thể tình nguyện viên mùa 3 cùng các chiến sĩ biên phòng và nhà trường tại lễ bàn giao",
    ],
    "season_04": [
        "Ngày hội tuyên truyền phòng chống đuối nước “Phao xinh cho em” tại xã Triệu Vân",
        "Các em học sinh hào hứng tham gia trò chơi nhận biết nguy cơ đuối nước",
        "Hướng dẫn trực quan kỹ năng an toàn dưới nước cho trẻ em vùng gần biển Triệu Lăng",
        "Trao tặng 34 suất quà khuyến học dịp Tết Ất Tỵ cho học sinh vượt khó",
        "Bàn giao bảng tuyên truyền kỹ năng phòng chống đuối nước cho Trường TH&THCS Triệu Vân",
        "Không khí rộn ràng tại Gian hàng Tết gây quỹ của học sinh Quảng Trị",
    ],
    "season_05": [
        "Buổi học chuyên đề kỹ năng sơ cứu cơ bản “An toàn cho em” tại Trường TH&THCS Tân Thành",
        "Hướng dẫn thực hành băng bó vết thương và xử lý tình huống khẩn cấp cho học sinh",
        "Trao tặng 100 đôi giày mới và hơn 100 suất quà khuyến học tại xã Tân Thành",
        "Bàn giao 04 bộ sơ cấp cứu loại A chuẩn Bộ Y Tế cho y tế học đường Tân Thành",
    ],
    "season_06": [
        "Nụ cười ấm áp của học sinh Trường PTDTBT Tiểu học Vĩnh Ô trong chiếc áo khoác mới",
        "Trao tặng 67 suất quà Tết và 03 bộ sơ cấp cứu loại A tại xã vùng sâu Vĩnh Ô",
        "Những cánh tay nhỏ nhắn hào hứng giơ cao trong tiết học kỹ năng tự bảo vệ",
        "Buổi hướng dẫn kỹ năng sơ cứu cơ bản “An toàn cho em 2” giữa mùa đông Vĩnh Linh",
        "Tình nguyện viên CHO EM mùa 6 ân cần trò chuyện cùng các em học sinh đồng bào Vân Kiều",
        "Khoảnh khắc kỷ niệm đáng nhớ của đoàn tình nguyện cùng thầy trò Trường PTDTBT TH Vĩnh Ô",
    ],
    "season_07": [
        "Nụ cười trong trẻo của học sinh Trường Tiểu học Tà Long ngày đón đoàn tình nguyện",
        "Trao tặng 125 chiếc áo phao cứu sinh cho các em nhỏ vùng sông suối Đakrông",
        "Bàn giao 02 “Tủ sách tri thức” cùng 345 đầu sách thiếu nhi cho thư viện điểm trường Pa Hy",
        "Tình nguyện viên CHO EM mùa 7 buộc dây cầu chúc bình an và trao học phẩm năm học mới",
        "Buổi tuyên truyền kỹ năng phòng chống đuối nước sinh động tại Trường Tiểu học Tà Long",
        "Khoảnh khắc gắn kết đầy yêu thương giữa học sinh Đông Hà và các em nhỏ Tà Long",
    ],
}


def normalize_smart_quotes(text: str) -> str:
    if not text:
        return ""
    for old_phrase, new_phrase in TITLE_CASE_PHRASE_FIXES:
        text = text.replace(old_phrase, new_phrase)
    text = re.sub(r'"([^"\n]{1,120})"', r"“\1”", text)
    text = re.sub(r"(?<!\w)'([^'\n]{2,120})'(?!\w)", r"“\1”", text)
    text = re.sub(r"“+([^”]+)”+", r"“\1”", text)
    return text


def normalize_vn_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = re.sub(r"[\u200b\u200c\u200d\ufeff\ufe0e\ufe0f]", "", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalize_smart_quotes(normalized.strip())


def to_natural_vietnamese_sentence_case(raw_title: str) -> str:
    """Convert shouting ALL-CAPS Vietnamese headlines into natural sentence case
    while preserving proper nouns, acronyms, and quoted campaign names."""
    s = raw_title.strip()
    if not s:
        return s
    s = s.lower()

    # Capitalize the very first letter and letters after colons, em-dashes, hyphens, or opening quotes
    s = re.sub(r"(^|[—–:\.\!\?]\s+|“)(\w)", lambda m: m.group(1) + m.group(2).upper(), s)

    # Restore proper nouns and acronyms
    for pattern, repl in PROPER_NOUN_REPLACEMENTS:
        s = re.sub(pattern, repl, s, flags=re.IGNORECASE)

    # Ensure first character is uppercase
    if s and s[0].isalpha():
        s = s[0].upper() + s[1:]

    return normalize_smart_quotes(s)


def clean_post_title(raw_caption: str, fallback_summary: str) -> str:
    norm_cap = normalize_vn_text(raw_caption)
    lines = [ln.strip() for ln in norm_cap.splitlines() if ln.strip()]
    first_line = lines[0] if lines else normalize_vn_text(fallback_summary)

    first_line = re.sub(r"^[\|\[\]【】\s]+|[\|\[\]【】\s]+$", "", first_line)
    first_line = re.sub(r"^[^\wÀ-ỹ\"“”‘’\(\)]+", "", first_line).strip()
    first_line = re.sub(r"[^\wÀ-ỹ\"“”‘’\.\!\?\)\]]+$", "", first_line).strip()

    first_line = re.sub(r"^CHO\s+EM\s*[:\|\-–—]\s*", "", first_line, flags=re.IGNORECASE).strip()
    first_line = re.sub(r"^NEWS\s*[:\|\-–—]\s*", "", first_line, flags=re.IGNORECASE).strip()

    if first_line.count("“") > first_line.count("”"):
        first_line += "”"
    if first_line.count('"') % 2 == 1:
        first_line += '"'

    if not first_line:
        first_line = normalize_vn_text(fallback_summary)

    return to_natural_vietnamese_sentence_case(first_line)


def split_body_and_footer(raw_caption: str) -> tuple[str, list[str]]:
    norm = normalize_vn_text(raw_caption)
    hashtags = re.findall(r"#[A-Za-z0-9_À-ỹ]+", norm)

    lines = norm.splitlines()
    body_lines = lines[1:] if len(lines) > 1 else lines

    cleaned_lines = []
    for ln in body_lines:
        s = ln.strip()
        if not s:
            cleaned_lines.append("")
            continue
        if re.match(r"^[_\-─━═\*]{5,}$", s):
            break
        if re.match(r"^(Mọi thông tin chi tiết|Thông tin liên hệ|Liên hệ với chúng mình)", s, flags=re.IGNORECASE):
            break
        if re.match(r"^(#[A-Za-z0-9_À-ỹ]+\s*)+$", s):
            continue
        cleaned_lines.append(s)

    body_clean = "\n".join(cleaned_lines).strip()
    body_clean = re.sub(r"\n{3,}", "\n\n", body_clean)
    if not body_clean:
        body_clean = norm
    return body_clean, hashtags


def classify_post(title_clean: str, body_clean: str) -> tuple[str, str]:
    upper = (title_clean + " " + body_clean[:200]).upper()
    if any(k in upper for k in ["NHÀ TÀI TRỢ", "ĐƠN VỊ ĐỒNG HÀNH", "TRI ÂN NHÀ TÀI TRỢ", "CẢM ƠN NHÀ TÀI TRỢ", "BẢO TRỢ"]):
        return "sponsor", "Cảm ơn nhà tài trợ"
    if any(k in upper for k in ["TỔNG KẾT", "RECAP CHƯƠNG TRÌNH", "VIDEO RECAP", "CHUYẾN ĐI CHO EM", "NHỮNG KHOẢNH KHẮC QUÝ GIÁ", "NHÌN LẠI HÀNH TRÌNH", "RECAP 2025", "LỄ KHÁNH THÀNH"]):
        return "recap", "Tổng kết chuyến đi"
    if any(k in upper for k in ["TUYỂN THÀNH VIÊN", "TUYỂN QUÂN", "CORE TEAM", "BAN TỔ CHỨC", "PHỎNG VẤN", "ỨNG VIÊN", "ĐƠN ĐĂNG KÝ", "GIA ĐÌNH CHO EM"]):
        return "team", "Thành viên & tuyển quân"
    if any(k in upper for k in ["SƠ CỨU", "ĐUỐI NƯỚC", "RĂNG MIỆNG", "CẨM NANG", "KỸ NĂNG", "MINIGAME", "GIẢI Ô CHỮ"]):
        return "knowledge", "Chia sẻ kiến thức"
    return "campaign", "Gây quỹ & chuẩn bị"


def build_web_bundle():
    project_info = json.loads((ROOT / "data/processed/project_info.json").read_text(encoding="utf-8"))
    page_info = json.loads((ROOT / "data/raw/page_info.json").read_text(encoding="utf-8"))
    seasons = json.loads((ROOT / "data/processed/seasons.json").read_text(encoding="utf-8"))
    programs = json.loads((ROOT / "data/processed/programs.json").read_text(encoding="utf-8"))
    journeys = json.loads((ROOT / "data/processed/journeys.json").read_text(encoding="utf-8"))
    milestones = json.loads((ROOT / "data/processed/milestones.json").read_text(encoding="utf-8"))
    stories = json.loads((ROOT / "data/processed/stories.json").read_text(encoding="utf-8"))
    timeline = json.loads((ROOT / "data/processed/timeline.json").read_text(encoding="utf-8"))
    posts = json.loads((ROOT / "data/raw/posts.json").read_text(encoding="utf-8"))
    photos = json.loads((ROOT / "data/raw/photos.json").read_text(encoding="utf-8"))
    videos = json.loads((ROOT / "data/raw/videos.json").read_text(encoding="utf-8"))
    albums = json.loads((ROOT / "data/raw/albums.json").read_text(encoding="utf-8"))

    photos_by_id = {p["photo_id"]: p for p in photos}
    videos_by_id = {v["video_id"]: v for v in videos}
    programs_by_id = {p["program_id"]: p for p in programs}
    stories_by_id = {s["story_id"]: s for s in stories}

    for ev in timeline:
        ev_id = ev.get("event_id", "")
        if ev_id in TIMELINE_TITLE_OVERRIDES:
            new_title, new_desc = TIMELINE_TITLE_OVERRIDES[ev_id]
            ev["title"] = new_title
            if new_desc:
                ev["description"] = new_desc
            else:
                ev["description"] = normalize_smart_quotes(ev.get("description", ""))
        else:
            ev["title"] = normalize_smart_quotes(ev.get("title", ""))
            ev["description"] = normalize_smart_quotes(ev.get("description", ""))

    cleaned_posts_map = {}
    for p in posts:
        pid = p["post_id"]
        title_clean = clean_post_title(p.get("caption_original", ""), p.get("summary", ""))
        body_clean, hashtags = split_body_and_footer(p.get("caption_original", ""))
        cat_id, cat_label = classify_post(title_clean, body_clean)
        cleaned_posts_map[pid] = {
            "title_clean": title_clean,
            "body_clean": body_clean,
            "caption_normalized": normalize_vn_text(p.get("caption_original", "")),
            "hashtags": hashtags[:8],
            "category_id": cat_id,
            "category_label": cat_label,
        }

    covers = [p for p in photos if p.get("category") == "cover_photo"]
    logos = [p for p in photos if p.get("category") == "project_logo"]

    CATEGORY_PRIORITY = {"recap": 0, "campaign": 1, "knowledge": 2, "team": 3, "sponsor": 4}

    enriched_seasons = []
    for s in seasons:
        sid = s["season_id"]
        typo = SEASON_TYPOGRAPHY_OVERRIDES.get(sid, {})
        if "official_name" in typo:
            s["official_name"] = typo["official_name"]
        if "theme" in typo:
            s["theme"] = typo["theme"]
        if "slogan" in typo:
            s["slogan"] = typo["slogan"]
        s["description"] = normalize_smart_quotes(s.get("description", ""))

        s_posts = [p for p in posts if sid in p.get("season_ids", [])]
        s_photos = [photos_by_id[pid] for pid in s["photo_ids"] if pid in photos_by_id]
        s_videos = [videos_by_id[vid] for vid in s["video_ids"] if vid in videos_by_id]
        s_prog = programs_by_id.get(s["program_ids"][0]) if s.get("program_ids") else None
        s_story = stories_by_id.get(f"story_{sid}") or (
            stories_by_id.get(s["story_ids"][0]) if s.get("story_ids") else None
        )
        if s_story:
            s_story = dict(s_story)
            if "story_title" in typo:
                s_story["title"] = typo["story_title"]
            s_story["summary"] = normalize_smart_quotes(s_story.get("summary", ""))
            s_story["narrative"] = normalize_smart_quotes(s_story.get("narrative", ""))

        hero_photo = CURATED_SEASON_HERO_PHOTOS.get(sid)
        if not hero_photo:
            landscape_photos = [p for p in s_photos if (p.get("width") or 0) >= (p.get("height") or 1)]
            hero_photo = (
                landscape_photos[0]["local_path"]
                if landscape_photos
                else (s_photos[0]["local_path"] if s_photos else None)
            )

        # Build resolved photos with rich, varied contextual descriptions
        resolved_photos = []
        if sid == "season_05":
            for item in SEASON_05_EXTRACTED_PHOTOS:
                resolved_photos.append(
                    {
                        **item,
                        "category_id": "recap",
                        "category_label": "Tổng kết chuyến đi",
                        "post_id": "post_3e14d54ba0b087b93146720f",
                        "has_bottom_banner": False,
                    }
                )

        post_photo_counters: dict[str, int] = {}
        moment_templates = ALBUM_MOMENT_DESCRIPTIONS.get(sid, [])

        for p in s_photos:
            raw_desc = normalize_vn_text(p.get("description", ""))
            parent_pid = p["post_ids"][0] if p.get("post_ids") else None
            parent_clean = cleaned_posts_map.get(parent_pid, {})
            parent_title = parent_clean.get("title_clean") or s["official_name"]
            parent_body = parent_clean.get("body_clean") or s["description"]
            cat_id = parent_clean.get("category_id", "recap")
            cat_label = parent_clean.get("category_label", "Hình ảnh chuyến đi")

            idx_in_post = post_photo_counters.get(parent_pid or "none", 0)
            post_photo_counters[parent_pid or "none"] = idx_in_post + 1

            is_generic = (
                not raw_desc
                or raw_desc.lower() in {"ảnh", "tải lên từ di động", "ảnh trên dòng thời gian"}
                or raw_desc.startswith("Ảnh tư liệu chính thức từ trang CHO EM")
            )
            caption_clean = parent_body if is_generic else raw_desc

            if p["local_path"] in BESPOKE_PHOTO_TITLES:
                short_title = BESPOKE_PHOTO_TITLES[p["local_path"]]
            elif not is_generic:
                short_title = clean_post_title(raw_desc, parent_title)
            else:
                if cat_id == "recap" and moment_templates:
                    template_str = moment_templates[idx_in_post % len(moment_templates)]
                    short_title = f"{template_str} (Khoảnh khắc #{idx_in_post + 1:02d})"
                elif idx_in_post > 0:
                    short_title = f"{parent_title} (Hình #{idx_in_post + 1:02d})"
                else:
                    short_title = parent_title

            w = p["width"] or 960
            h = p["height"] or 720
            has_bottom_banner = bool(
                (sid == "season_07" and w == 1769 and h == 1365)
                or parent_pid in {"post_3c45223081d6ba4f89f28445", "post_1e4fd5805d400146d889cfb4"}
            )

            resolved_photos.append(
                {
                    "photo_id": p["photo_id"],
                    "local_path": p["local_path"],
                    "width": w,
                    "height": h,
                    "published_at": p["published_at"],
                    "title_clean": short_title,
                    "description": caption_clean,
                    "category_id": cat_id,
                    "category_label": cat_label,
                    "post_id": parent_pid,
                    "has_bottom_banner": has_bottom_banner,
                }
            )

        highlight_paths = CURATED_SEASON_HIGHLIGHTS.get(sid, [])

        def photo_sort_key(item):
            if item["local_path"] == hero_photo:
                return (-2, 0)
            if item["local_path"] in highlight_paths:
                return (-1, highlight_paths.index(item["local_path"]))
            cat_rank = CATEGORY_PRIORITY.get(item["category_id"], 3)
            return (cat_rank, 0)

        resolved_photos.sort(key=photo_sort_key)

        resolved_videos = []
        for v in s_videos:
            v_title = clean_post_title(v.get("caption_original", ""), s["official_name"])
            v_body, _ = split_body_and_footer(v.get("caption_original", ""))
            resolved_videos.append(
                {
                    "video_id": v["video_id"],
                    "local_path": v["local_path"],
                    "width": v["width"] or 1280,
                    "height": v["height"] or 720,
                    "duration_seconds": v["duration_seconds"],
                    "published_at": v["published_at"],
                    "title_clean": v_title,
                    "body_clean": v_body,
                    "caption_original": normalize_vn_text(v.get("caption_original", "")),
                }
            )

        resolved_posts = []
        for p in s_posts:
            pid = p["post_id"]
            c_info = cleaned_posts_map[pid]
            p_photos = [
                photos_by_id[ph_id]["local_path"]
                for ph_id in p["photo_ids"]
                if ph_id in photos_by_id
            ]
            if pid == "post_3e14d54ba0b087b93146720f" and not p_photos:
                p_photos = [x["local_path"] for x in SEASON_05_EXTRACTED_PHOTOS[:4]]

            resolved_posts.append(
                {
                    "post_id": pid,
                    "published_at": p["published_at"],
                    "title_clean": c_info["title_clean"],
                    "summary": c_info["title_clean"],
                    "body_clean": c_info["body_clean"],
                    "caption_original": c_info["caption_normalized"],
                    "category_id": c_info["category_id"],
                    "category_label": c_info["category_label"],
                    "hashtags": c_info["hashtags"],
                    "post_type": p["post_type"],
                    "post_url": p["post_url"],
                    "photo_paths": p_photos,
                    "video_paths": [
                        videos_by_id[vid]["local_path"]
                        for vid in p["video_ids"]
                        if vid in videos_by_id
                    ],
                    "locations": p["location_mentions"],
                }
            )

        resolved_posts.sort(
            key=lambda item: (CATEGORY_PRIORITY.get(item["category_id"], 3), item["published_at"] or ""),
        )

        enriched_seasons.append(
            {
                **s,
                "hero_photo": hero_photo,
                "highlight_photos": highlight_paths,
                "program": s_prog,
                "story": s_story,
                "posts_count": len(resolved_posts),
                "photos_count": len(resolved_photos),
                "videos_count": len(resolved_videos),
                "resolved_photos": resolved_photos,
                "resolved_videos": resolved_videos,
                "resolved_posts": resolved_posts,
            }
        )

    bundle = {
        "generated_at": "2026-11-18T01:28:00+07:00",
        "project_info": project_info,
        "page_info": page_info,
        "stats": {
            "total_seasons": len(seasons),
            "total_posts": len(posts),
            "total_photos": sum(len(s["resolved_photos"]) for s in enriched_seasons),
            "total_videos": len(videos),
            "total_programs": len(programs),
            "total_journeys": len(journeys),
            "years_active": "2023 – 2026",
            "founded_date": "17/07/2023",
        },
        "covers": [c["local_path"] for c in covers],
        "logos": [l["local_path"] for l in logos],
        "seasons": enriched_seasons,
        "timeline": timeline,
        "milestones": milestones,
        "stories": stories,
        "albums": albums,
    }

    out_dir = ROOT / "website/data"
    out_dir.mkdir(parents=True, exist_ok=True)
    js_content = "window.CHO_EM_ARCHIVE = " + json.dumps(bundle, ensure_ascii=False, indent=2) + ";\n"
    (out_dir / "archive_bundle.js").write_text(js_content, encoding="utf-8")
    (out_dir / "archive_bundle.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote normalized website/data/archive_bundle.js ({len(js_content)/1024:.1f} KB)")


if __name__ == "__main__":
    build_web_bundle()
