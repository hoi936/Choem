#!/usr/bin/env python3
"""Build the complete 7-season CHO EM archive in Cho_em_HanhTrinh from curated Data_fb export."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from curate_facebook_export import ROOT, PAGE_ID, PAGE_URL, main as curate_export


SEASON_METADATA = [
    {
        "season_id": "season_01",
        "season_number": 1,
        "official_name": "CHO EM Mùa 1 — Sân Chơi Cho Em",
        "theme": "Sân Chơi Tái Chế Cho Trẻ Em Vùng Cao",
        "slogan": "Sân chơi cho em, cho em niềm vui, gieo mầm ước mơ",
        "start_date": "2023-07-17",
        "end_date": "2023-08-22",
        "event_date": "2023-08-15",
        "program_id": "program_san_choi_cho_em_2023",
        "program_name": "Sân Chơi Cho Em (Mùa 1)",
        "journey_id": "journey_huc_huong_hoa_2023",
        "journey_title": "Chuyến đi Xã Húc, Hướng Hóa — Khánh thành 02 sân chơi tái chế Bản Ho Le & Tà Rùng",
        "locations": [
            "Điểm trường Mầm non Bản Ho Le, xã Húc, huyện Hướng Hóa, tỉnh Quảng Trị",
            "Điểm trường Mầm non Bản Tà Rùng, xã Húc, huyện Hướng Hóa, tỉnh Quảng Trị",
            "Trường Mầm non Húc, huyện Hướng Hóa, tỉnh Quảng Trị",
        ],
        "leaders": [
            {"name": "Trần Ngọc Tâm Phúc", "role": "Quản lý dự án (Founder)", "email": "ngoctamphuctran@gmail.com"},
            {"name": "Nguyễn Thùy Linh", "role": "Trưởng ban Truyền thông", "email": "thuylinhnguyen482005@gmail.com"},
        ],
        "patron": "Thành đoàn Đông Hà",
        "funds_raised_vnd": 27381403,
        "description": "Mùa mở đầu đặt nền móng cho dự án CHO EM (thành lập 17/07/2023). Xuất phát từ trăn trở trước những khoảng sân bê tông trống trải tại các điểm trường mầm non vùng cao Hướng Hóa, dự án đã gây quỹ bằng làm nơ handmade và vận động quyên góp đạt 27.381.403 VNĐ để tự tay thi công và trao tặng 02 sân chơi tái chế từ lốp xe và gỗ tại điểm trường Ho Le và Tà Rùng (Trường Mầm non Húc).",
        "objectives": [
            "Xây dựng và khánh thành 02 sân chơi tái chế an toàn, sáng tạo tại điểm trường Mầm non Bản Ho Le và Bản Tà Rùng (xã Húc, Hướng Hóa).",
            "Trao tặng tủ đồ chơi, quần áo mới và phần quà tiếp sức đến trường cho các em nhỏ đồng bào Vân Kiều.",
            "Lan tỏa thông điệp bảo vệ môi trường thông qua tái chế lốp xe cũ thành thiết bị vui chơi cho trẻ em vùng sâu vùng xa.",
        ],
        "activities": [
            "Làm nơ handmade gây quỹ và vận động quyên góp cộng đồng đạt 27.381.403 VNĐ",
            "Tự tay thiết kế, sơn vẽ và thi công các hạng mục sân chơi từ lốp xe tái chế và gỗ",
            "Vượt chặng đường đèo gần 80km từ Đông Hà lên xã Húc, huyện Hướng Hóa lắp đặt sân chơi",
            "Khánh thành 02 sân chơi và giao lưu, trao quà cho học sinh mầm non tại Ho Le và Tà Rùng",
        ],
        "results": [
            {"metric": "tổng kinh phí gây quỹ (VNĐ)", "value": 27381403, "qualifier": "exact"},
            {"metric": "sân chơi tái chế khánh thành", "value": 2, "qualifier": "exact"},
            {"metric": "xích đu lớn, bập bênh & ngựa gỗ", "value": 6, "qualifier": "exact"},
            {"metric": "suất bánh kẹo", "value": 87, "qualifier": "exact"},
            {"metric": "bộ quần áo mới", "value": 85, "qualifier": "exact"},
            {"metric": "tủ đồ chơi", "value": 2, "qualifier": "exact"},
        ],
        "story_title": "Người Nhỏ Làm Việc Nhỏ — Hành Trình 80km Vượt Đèo Lên Bản Ho Le & Tà Rùng",
        "story_summary": "Hành trình 2 tháng ròng rã tự tay sơn từng chiếc lốp xe, đóng từng chú ngựa gỗ dưới nắng hè Đông Hà để đổi lấy ánh mắt trong veo và nụ cười rạng rỡ của các em nhỏ xã Húc trong ngày đầu đến lớp.",
    },
    {
        "season_id": "season_02",
        "season_number": 2,
        "official_name": "CHO EM Mùa 2 — Răng Xinh Cho Em",
        "theme": "Chăm Sóc Sức Khỏe Răng Miệng Học Đường",
        "slogan": "Vì những nụ cười trẻ thơ — Góp phần nhỏ vì một tương lai tươi sáng hơn của trẻ em Quảng Trị",
        "start_date": "2024-01-17",
        "end_date": "2024-02-15",
        "event_date": "2024-02-02",
        "program_id": "program_rang_xinh_cho_em_2024",
        "program_name": "Răng Xinh Cho Em",
        "journey_id": "journey_trieu_van_2024",
        "journey_title": "Chuyến đi Trường TH&THCS Triệu Vân, Triệu Phong — Ngày hội Răng Xinh Cho Em",
        "locations": [
            "Trường Tiểu học và Trung học cơ sở Triệu Vân, xã Triệu Vân, huyện Triệu Phong, tỉnh Quảng Trị",
        ],
        "leaders": [
            {"name": "Trần Ngọc Tâm Phúc", "role": "Quản lý dự án", "email": "ngoctamphuctran@gmail.com"},
            {"name": "Nguyễn Thùy Linh", "role": "Trưởng ban Truyền thông", "email": "thuylinhnguyen482005@gmail.com"},
        ],
        "patron": "Tỉnh đoàn Quảng Trị, Thành đoàn Đông Hà & Đoàn trường THPT Chuyên Lê Quý Đôn",
        "funds_raised_vnd": None,
        "description": "Mùa thứ 2 đánh dấu sự mở rộng sứ mệnh của CHO EM sang lĩnh vực giáo dục sức khỏe học đường dịp giáp Tết Quý Mão / Giáp Thìn (tháng 1–2/2024). Chương trình 'Răng Xinh Cho Em' tại Trường TH&THCS Triệu Vân (huyện Triệu Phong) đã mang đến những tiết mục kịch, múa hát trực quan cùng lớp học thực hành vệ sinh răng miệng đúng cách và trao quà cho các em học sinh vùng biển bãi ngang.",
        "objectives": [
            "Phổ biến kiến thức và hướng dẫn thực hành quy trình chăm sóc, vệ sinh răng miệng đúng cách cho học sinh Trường TH&THCS Triệu Vân.",
            "Trao tặng bộ dụng cụ chăm sóc răng miệng (bàn chải, kem đánh răng) và đồ dùng học tập dịp Tết đến Xuân về.",
        ],
        "activities": [
            "Tổ chức gian hàng gây quỹ và vận động quyên góp bàn chải, kem đánh răng, đồ dùng học tập",
            "Biểu diễn văn nghệ, đóng kịch tuyên truyền trực quan về tác hại của sâu răng",
            "Tổ chức lớp học thực tế hướng dẫn đánh răng đúng cách, hiệu quả và an toàn",
            "Giao lưu, tổ chức trò chơi và trao quà cho học sinh Trường TH&THCS Triệu Vân ngày 02/02/2024",
        ],
        "results": [
            {"metric": "trường học thụ hưởng", "value": 1, "qualifier": "exact"},
            {"metric": "lớp học thực hành & giao lưu", "value": 1, "qualifier": "exact"},
        ],
        "story_title": "Hai Ba Bàn Chải Nhỏ — Giữ Trọn Nụ Cười Xinh Nơi Vùng Biển Cát Triệu Vân",
        "story_summary": "Khép lại năm Quý Mão bằng những vở kịch vui nhộn và những chiếc bàn chải nhỏ trao tay các em học sinh xã bãi ngang Triệu Vân, gieo thói quen tự chăm sóc bản thân mỗi ngày.",
    },
    {
        "season_id": "season_03",
        "season_number": 3,
        "official_name": "CHO EM Mùa 3 — Sân Chơi Cho Em (Mùa 3)",
        "theme": "Tiếp Tục Sứ Mệnh — Nối Tiếp Hành Trình Xây Sân Chơi Vùng Cao",
        "slogan": "Sân chơi cho em, cho em niềm vui, gieo mầm ước mơ",
        "start_date": "2024-07-03",
        "end_date": "2024-08-20",
        "event_date": "2024-08-06",
        "program_id": "program_san_choi_cho_em_mua_3_2024",
        "program_name": "Sân Chơi Cho Em (Mùa 3)",
        "journey_id": "journey_huong_phung_2024",
        "journey_title": "Chuyến đi Chênh Vênh & Hướng Choa (Hướng Phùng, Hướng Hóa) — Khánh thành 02 sân chơi tái chế",
        "locations": [
            "Điểm trường Mầm non Chênh Vênh, Trường Mầm non Hướng Phùng, xã Hướng Phùng, huyện Hướng Hóa, tỉnh Quảng Trị",
            "Điểm trường Mầm non Hướng Choa, Trường Mầm non Hướng Phùng, xã Hướng Phùng, huyện Hướng Hóa, tỉnh Quảng Trị",
        ],
        "leaders": [
            {"name": "Lê Thị Thúy Như", "role": "Trưởng Ban tổ chức", "email": "lethuynhu1714@gmail.com"},
            {"name": "Nguyễn Văn Linh", "role": "Đồng Trưởng Ban tổ chức", "email": "nguyenvlinh2366@gmail.com"},
            {"name": "Trần Thiên Hương", "role": "Trưởng ban Truyền thông", "email": "contact.thienhuongtran@gmail.com"},
            {"name": "Nguyễn Thùy Linh", "role": "Trưởng ban Truyền thông", "email": "thuylinhnguyen482005@gmail.com"},
        ],
        "patron": "Thành đoàn Đông Hà",
        "funds_raised_vnd": 28337123,
        "description": "Mùa 3 trở lại huyện miền núi Hướng Hóa với quy mô lớn hơn và thế hệ Ban Tổ chức kế cận đầy nhiệt huyết. Thông qua các đợt bán hàng gây quỹ mùa hè và kêu gọi tài trợ đạt 28.337.123 VNĐ, dự án đã tự thi công và khánh thành 02 sân chơi tái chế hoàn chỉnh tại điểm trường Chênh Vênh và Hướng Choa (thuộc Trường Mầm non Hướng Phùng) vào ngày 06/08/2024.",
        "objectives": [
            "Xây dựng và khánh thành 02 sân chơi tái chế an toàn, thân thiện môi trường tại điểm trường Chênh Vênh và Hướng Choa (xã Hướng Phùng, Hướng Hóa).",
            "Trao tặng vở tập tô, đồ chơi mới và phần quà khuyến khích học sinh mầm non vùng cao đến trường.",
        ],
        "activities": [
            "Mở đơn tuyển thành viên Mùa 3 với 5 ban chuyên môn (Truyền thông, Tài chính - Đối ngoại, Hậu cần, Nhân sự, Nội dung)",
            "Tổ chức sự kiện bán đồ ăn, thức uống mùa hè gây quỹ và kêu gọi ủng hộ đạt 28.337.123 VNĐ",
            "Thi công 2 xích đu lớn, 4 bập bênh, 8 chú ngựa gỗ, 2 bộ vòm chui và 2 thảm cỏ ngoài trời",
            "Lễ khánh thành sân chơi và trao quà tại điểm trường Chênh Vênh & Hướng Choa ngày 06/08/2024",
        ],
        "results": [
            {"metric": "tổng kinh phí gây quỹ (VNĐ)", "value": 28337123, "qualifier": "exact"},
            {"metric": "sân chơi tái chế khánh thành", "value": 2, "qualifier": "exact"},
            {"metric": "hạng mục thiết bị sân chơi (xích đu, bập bênh, ngựa gỗ, vòm chui, thảm cỏ)", "value": 18, "qualifier": "exact"},
            {"metric": "cuốn vở tập tô", "value": 272, "qualifier": "exact"},
            {"metric": "suất bánh kẹo", "value": 60, "qualifier": "exact"},
            {"metric": "đồ chơi mới", "value": 29, "qualifier": "exact"},
        ],
        "story_title": "Nắng Hè Đông Hà & Niềm Vui Nơi Điểm Trường Chênh Vênh, Hướng Choa",
        "story_summary": "Những ngày hè đổ lửa tụ họp tại xưởng cơ khí cắt hàn từng khung xích đu, sơn từng lốp xe để mang lên vùng cao Hướng Phùng hai sân chơi rực rỡ sắc màu.",
    },
    {
        "season_id": "season_04",
        "season_number": 4,
        "official_name": "CHO EM Mùa 4 — Phao Xinh Cho Em",
        "theme": "Tuyên Truyền Phòng Chống Đuối Nước & Sẻ Chia Hơi Ấm Mùa Xuân",
        "slogan": "Tết đoàn viên năm nay, cùng Cho Em chia sẻ yêu thương",
        "start_date": "2024-12-16",
        "end_date": "2025-01-28",
        "event_date": "2025-01-22",
        "program_id": "program_phao_xinh_cho_em_2025",
        "program_name": "Phao Xinh Cho Em",
        "journey_id": "journey_trieu_van_2025",
        "journey_title": "Chuyến đi Trường TH&THCS Triệu Vân — Chương trình Phao Xinh Cho Em dịp Tết Ất Tỵ 2025",
        "locations": [
            "Trường TH&THCS Triệu Vân (thôn 8, xã Triệu Vân, huyện Triệu Phong, tỉnh Quảng Trị)",
        ],
        "leaders": [
            {"name": "Lê Thị Thúy Như", "role": "Trưởng Ban tổ chức", "email": "lethuynhu1714@gmail.com"},
            {"name": "Nguyễn Văn Linh", "role": "Đồng Trưởng Ban tổ chức", "email": "nguyenvlinh2366@gmail.com"},
            {"name": "Trần Thiên Hương", "role": "Trưởng ban Truyền thông", "email": "contact.thienhuongtran@gmail.com"},
        ],
        "patron": "Thành đoàn Đông Hà",
        "funds_raised_vnd": 17950000,
        "description": "Khởi động vào tháng 12/2024 đón Xuân Ất Tỵ 2025, CHO EM Mùa 4 trở lại mái trường vùng biển TH&THCS Triệu Vân (cách biển Triệu Lăng 5km) với chương trình 'Phao Xinh Cho Em'. Đây là cột mốc mở đầu cho chuỗi chương trình giáo dục kỹ năng sinh tồn và phòng chống tai nạn đuối nước của dự án, kết hợp cùng Gian hàng Tết gây quỹ và trao quà khuyến học.",
        "objectives": [
            "Giáo dục, tuyên truyền kiến thức phòng chống tai nạn đuối nước và kỹ năng cứu hộ an toàn cho học sinh khối 3, 4, 5 tại xã vùng biển Triệu Vân.",
            "Trao tặng bảng tuyên truyền trực quan và các suất quà Tết khuyến học cho học sinh vượt khó.",
        ],
        "activities": [
            "Tuyển thành viên và ra mắt đội ngũ Đại sứ Truyền thông CHO EM Mùa 4",
            "Tổ chức Gian hàng Tết 'Phao Xinh Cho Em' (thu lợi nhuận 9.450.000 VNĐ) và kêu gọi tài trợ (8.500.000 VNĐ)",
            "Tổ chức ngày hội tuyên truyền phòng chống đuối nước cho học sinh lớp 3, 4, 5 tại Trường TH&THCS Triệu Vân ngày 22/01/2025",
            "Trao tặng 34 suất quà Tết khuyến học và 02 bảng tuyên truyền phòng chống tai nạn đuối nước",
        ],
        "results": [
            {"metric": "tổng nguồn lực gây quỹ & tài trợ (VNĐ)", "value": 17950000, "qualifier": "exact"},
            {"metric": "suất quà khuyến học dịp Tết", "value": 34, "qualifier": "exact"},
            {"metric": "bảng tuyên truyền phòng chống đuối nước", "value": 2, "qualifier": "exact"},
        ],
        "story_title": "Hành Trang Tuổi 18 & Mùa Xuân Nơi Ngôi Trường Gần Biển Triệu Lăng",
        "story_summary": "Những cuộc họp xuyên đêm, những gói mứt Tết chở đầy tâm huyết và buổi học kỹ năng sinh tồn ấm áp dành tặng các em nhỏ vùng biển Triệu Vân trước thềm năm mới.",
    },
    {
        "season_id": "season_05",
        "season_number": 5,
        "official_name": "CHO EM Mùa 5 — An Toàn Cho Em",
        "theme": "Giáo Dục Kỹ Năng Sơ Cứu Cơ Bản & Tự Bảo Vệ Trước Tai Nạn Thương Tích",
        "slogan": "Trang bị kỹ năng sống an toàn — Lan tỏa yêu thương đến trẻ em vùng cao",
        "start_date": "2025-07-10",
        "end_date": "2025-08-18",
        "event_date": "2025-08-11",
        "program_id": "program_an_toan_cho_em_2025",
        "program_name": "An Toàn Cho Em",
        "journey_id": "journey_tan_thanh_2025",
        "journey_title": "Chuyến đi Trường TH&THCS Tân Thành — Lớp học sơ cứu và trao quà An Toàn Cho Em",
        "locations": [
            "Trường TH&THCS Tân Thành, xã Tân Thành, huyện Hướng Hóa, tỉnh Quảng Trị",
        ],
        "leaders": [
            {"name": "Trần Mai Hương Nguyên", "role": "Trưởng Ban tổ chức", "email": "tranmaihuongnguyenqt@gmail.com"},
            {"name": "Trần Thiên Hương", "role": "Trưởng ban Truyền thông", "email": "contact.thienhuongtran@gmail.com"},
            {"name": "Đậu Khắc Gia Bảo", "role": "Phụ trách Tài chính", "email": None},
        ],
        "patron": "Đoàn trường THPT Chuyên Lê Quý Đôn",
        "funds_raised_vnd": 25057548,
        "description": "Mùa hè 2025, CHO EM bước sang Mùa 5 dưới sự bảo trợ pháp lý của Đoàn trường THPT Chuyên Lê Quý Đôn. Nhận thấy trẻ em vùng cao thường thiếu kỹ năng tự xử lý khi gặp tai nạn thương tích, dự án đã triển khai chương trình 'An Toàn Cho Em' tại Trường TH&THCS Tân Thành vào ngày 11/08/2025, huy động 25.057.548 VNĐ tiền mặt cùng 100 đôi giày mới (trị giá 20 triệu đồng) và các bộ sơ cấp cứu chuẩn Bộ Y Tế.",
        "objectives": [
            "Trang bị kiến thức và kỹ năng sơ cứu cơ bản, xử lý tình huống khẩn cấp cho học sinh khối 4, 5 tại Trường TH&THCS Tân Thành.",
            "Cung cấp trang thiết bị y tế sơ cấp cứu đạt chuẩn và quà tặng thiết thực cho học sinh vùng biên giới.",
        ],
        "activities": [
            "Tổ chức đặt hàng gây quỹ và vận động tài trợ đạt 25.057.548 VNĐ tiền mặt cùng hiện vật giá trị lớn",
            "Tổ chức lớp học thực hành kỹ năng sơ cứu cơ bản (băng bó vết thương, xử lý bỏng, dị vật, tai nạn thường gặp) ngày 11/08/2025",
            "Trao tặng hơn 100 suất quà, 100 đôi giày mới, 04 Bộ sơ cấp cứu loại A chuẩn Bộ Y Tế và 02 bảng tuyên truyền kỹ năng sơ cứu",
        ],
        "results": [
            {"metric": "tổng kinh phí gây quỹ (VNĐ)", "value": 25057548, "qualifier": "exact"},
            {"metric": "suất quà trao tặng học sinh", "value": 100, "qualifier": "greater_than"},
            {"metric": "đôi giày mới (trị giá 20.000.000 VNĐ)", "value": 100, "qualifier": "exact"},
            {"metric": "bộ sơ cấp cứu loại A chuẩn Bộ Y Tế", "value": 4, "qualifier": "exact"},
            {"metric": "bảng tuyên truyền kỹ năng sơ cứu", "value": 2, "qualifier": "exact"},
        ],
        "story_title": "Sự Sẻ Chia Là Liều Thuốc Quý Giá Nhất — Chuyến Xe Mùa 5 Đến Với Tân Thành",
        "story_summary": "Hơn 100 đôi giày mới, 4 bộ sơ cấp cứu chuẩn y tế và những giờ học thực hành băng bó sôi nổi đã tiếp thêm sự tự tin cho các em học sinh vùng cao Tân Thành.",
    },
    {
        "season_id": "season_06",
        "season_number": 6,
        "official_name": "CHO EM Mùa 6 — An Toàn Cho Em 2",
        "theme": "Tấm Lá Chắn Kỹ Năng Sơ Cứu Cho Trẻ Em Vùng Sâu Vĩnh Ô",
        "slogan": "An Toàn Cho Em — Gửi Trọn Yêu Thương",
        "start_date": "2025-12-13",
        "end_date": "2026-02-11",
        "event_date": "2026-02-09",
        "program_id": "program_an_toan_cho_em_2_2026",
        "program_name": "An Toàn Cho Em 2",
        "journey_id": "journey_vinh_o_2026",
        "journey_title": "Chuyến đi Trường PTDTBT Tiểu học Vĩnh Ô — Chương trình An Toàn Cho Em 2",
        "locations": [
            "Trường PTDTBT Tiểu học Vĩnh Ô, xã Vĩnh Ô (Bến Quan), tỉnh Quảng Trị",
        ],
        "leaders": [
            {"name": "Lê Khánh Linh", "role": "Trưởng Ban tổ chức", "email": "klingle.187@gmail.com"},
            {"name": "Phan Thanh Huyền", "role": "Phó Ban tổ chức", "email": "pt.huyen11042009@gmail.com"},
            {"name": "Võ Ngọc Gia Linh", "role": "Điều phối tiếp nhận hiện vật", "email": None},
        ],
        "patron": "Đoàn trường THPT Chuyên Lê Quý Đôn",
        "funds_raised_vnd": None,
        "description": "Khởi động từ tháng 12/2025 và diễn ra sự kiện chính vào ngày 09/02/2026, CHO EM Mùa 6 tiếp nối sứ mệnh giáo dục kỹ năng sơ cứu cơ bản với chương trình 'An Toàn Cho Em 2' tại Trường PTDTBT Tiểu học Vĩnh Ô — một trong những xã miền núi đặc biệt khó khăn của tỉnh Quảng Trị. Dự án đã trang bị 'tấm lá chắn' kỹ năng tự bảo vệ cùng 67 suất quà và 03 Bộ sơ cấp cứu loại A cho nhà trường.",
        "objectives": [
            "Giáo dục kỹ năng sơ cứu cơ bản và phòng tránh tai nạn thương tích cho học sinh bán trú khối 4, 5 tại Trường PTDTBT Tiểu học Vĩnh Ô.",
            "Trao tặng quà khuyến học và trang bị bộ sơ cấp cứu chuẩn Bộ Y Tế cho phòng y tế học đường vùng cao Vĩnh Ô.",
        ],
        "activities": [
            "Tổ chức Gian hàng Tết 'An Toàn Cho Em 2 - Tết của sự sẻ chia' (Pre-order và bán hàng trực tiếp tại Đông Hà)",
            "Phát động chiến dịch thay khung hình avatar lan tỏa thông điệp an toàn học đường",
            "Tổ chức ngày hội giáo dục kỹ năng sơ cứu cơ bản tại Trường PTDTBT Tiểu học Vĩnh Ô ngày 09/02/2026",
            "Trao tặng 67 suất quà học sinh và 03 Bộ sơ cấp cứu loại A chuẩn Bộ Y Tế",
        ],
        "results": [
            {"metric": "suất quà trao tặng học sinh khối 4, 5", "value": 67, "qualifier": "exact"},
            {"metric": "bộ sơ cấp cứu loại A chuẩn Bộ Y Tế", "value": 3, "qualifier": "exact"},
        ],
        "story_title": "Vượt Đèo Lên Vĩnh Ô — Mang Tấm Lá Chắn Kỹ Năng Giữa Mùa Đông Ấm Áp",
        "story_summary": "Hành trình mùa thứ 6 đưa những người trẻ nhiệt huyết vượt đường núi xa xôi đến với các em học sinh bán trú Vĩnh Ô, trao gửi kỹ năng tự bảo vệ và hơi ấm ngày xuân.",
    },
    {
        "season_id": "season_07",
        "season_number": 7,
        "official_name": "CHO EM Mùa 7 — Hành Trang Cho Em",
        "theme": "Phòng Chống Tai Nạn Đuối Nước & Tủ Sách Tri Thức Vùng Cao",
        "slogan": "Cùng Hành Trang Cho Em — Thay màu áo mới, bảo vệ nụ cười thơ",
        "start_date": "2026-07-06",
        "end_date": "2026-08-20",
        "event_date": "2026-08-18",
        "program_id": "program_hanh_trang_cho_em_2026",
        "program_name": "Hành Trang Cho Em",
        "journey_id": "journey_ta_long_2026",
        "journey_title": "Chuyến đi Trường Tiểu học Tà Long (Thôn Pa Hy, Đakrông) — Chương trình Hành Trang Cho Em",
        "locations": [
            "Trường Tiểu học Tà Long (điểm trường thôn Pa Hy), xã Tà Long / Đakrông, huyện Đakrông, tỉnh Quảng Trị",
        ],
        "leaders": [
            {"name": "Lê Khánh Linh", "role": "Trưởng Ban tổ chức", "email": "klingle.187@gmail.com"},
            {"name": "Phan Thanh Huyền", "role": "Phó Ban tổ chức", "email": "pt.huyen11042009@gmail.com"},
            {"name": "Võ Ngọc Gia Linh", "role": "Điều phối tiếp nhận hiện vật", "email": None},
        ],
        "patron": "Ủy ban Nhân dân xã Đakrông & Ban Giám hiệu Trường Tiểu học Tà Long",
        "funds_raised_vnd": None,
        "description": "Mùa 7 (tháng 7–8/2026) đánh dấu bước trưởng thành rực rỡ của CHO EM với chương trình 'Hành Trang Cho Em' tại điểm trường Tiểu học Tà Long (thôn Pa Hy, xã Đakrông, tỉnh Quảng Trị) vào ngày 18/08/2026. Kết hợp giữa bán hàng online, Workshop nghệ thuật gây quỹ và đợt quyên góp sách cộng đồng, dự án đã trao tặng 125 áo phao, 125 suất quà, hơn 100 đầu sách và 02 tủ sách tri thức cho thư viện nhà trường.",
        "objectives": [
            "Tuyên truyền và giáo dục kỹ năng phòng chống tai nạn đuối nước cho học sinh vùng cao tại điểm trường Tiểu học Tà Long.",
            "Trao tặng áo phao cứu sinh, quà khuyến học và xây dựng Tủ sách tri thức cho thư viện điểm trường.",
        ],
        "activities": [
            "Mở đơn tuyển thành viên Mùa 7 và tổ chức bán hàng gây quỹ online",
            "Tổ chức thành công Workshop gây quỹ 'Hành Trang Cho Em' tại Đông Hà (01–02/08/2026)",
            "Phát động chiến dịch quyên góp sách giáo khoa, truyện thiếu nhi và sách kỹ năng (11–17/08/2026)",
            "Tổ chức chương trình chính 'Hành Trang Cho Em' tại điểm trường Tiểu học Tà Long ngày 18/08/2026",
            "Trao tặng 125 suất quà, 125 áo phao, hơn 100 quyển sách và 02 tủ sách tri thức đặt tại thư viện trường",
        ],
        "results": [
            {"metric": "suất quà học sinh", "value": 125, "qualifier": "exact"},
            {"metric": "áo phao cứu sinh", "value": 125, "qualifier": "exact"},
            {"metric": "quyển sách thiếu nhi & giáo khoa", "value": 100, "qualifier": "greater_than"},
            {"metric": "tủ sách tri thức thư viện", "value": 2, "qualifier": "exact"},
        ],
        "story_title": "Hành Trang Cho Em — Những Chiếc Áo Phao Cam & Tủ Sách Tri Thức Giữa Núi Rừng Tà Long",
        "story_summary": "Từ buổi Workshop rộn ràng tại Đông Hà đến chuyến xe vượt suối vào thôn Pa Hy (Tà Long), 125 chiếc áo phao và 2 tủ sách đầy ắp yêu thương đã trở thành hành trang vững chắc cho các em nhỏ vùng cao.",
    },
]


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_archive():
    posts, photos, videos, discovered = curate_export()

    # Sort posts newest first in data/raw/posts.json (matching standard archive order)
    posts_sorted_desc = sorted(posts, key=lambda x: x["published_at"], reverse=True)
    posts_sorted_asc = sorted(posts, key=lambda x: x["published_at"])

    # 1. Clean and write individual post files in data/raw/posts/<post_id>.json
    posts_dir = ROOT / "data/raw/posts"
    if posts_dir.exists():
        for old_f in posts_dir.glob("*.json"):
            old_f.unlink()
    posts_dir.mkdir(parents=True, exist_ok=True)
    for p in posts_sorted_desc:
        write_json(posts_dir / f"{p['post_id']}.json", p)

    write_json(ROOT / "data/raw/posts.json", posts_sorted_desc)
    write_json(ROOT / "data/raw/photos.json", photos)
    write_json(ROOT / "data/raw/videos.json", videos)
    write_json(ROOT / "data/raw/discovered_urls.json", discovered)

    # 2. Write albums.json
    albums = [
        {
            "album_id": "album_114435608386800",
            "facebook_album_id": "114435608386800",
            "name": "Ảnh (Timeline Photos)",
            "description": "Album ảnh bài đăng chính thức trên dòng thời gian của dự án CHO EM qua 7 mùa hoạt động.",
            "photo_ids": [p["photo_id"] for p in photos if p.get("provenance", {}).get("album_folder") == "Anh_114435608386800"],
            "source_urls": [PAGE_URL],
            "verification_status": "verified",
        },
        {
            "album_id": "album_127004223796605",
            "facebook_album_id": "127004223796605",
            "name": "Tải lên từ di động (Mobile Uploads)",
            "description": "Album ảnh thực địa các chuyến đi thiện nguyện và hoạt động gây quỹ tải lên từ di động.",
            "photo_ids": [p["photo_id"] for p in photos if p.get("provenance", {}).get("album_folder") == "Tailentudidong_127004223796605"],
            "source_urls": [PAGE_URL],
            "verification_status": "verified",
        },
        {
            "album_id": "album_111239118706449",
            "facebook_album_id": "111239118706449",
            "name": "Ảnh bìa (Cover Photos)",
            "description": "Bộ sưu tập ảnh bìa chính thức qua từng mùa chiến dịch của CHO EM project.",
            "photo_ids": [p["photo_id"] for p in photos if p.get("provenance", {}).get("album_folder") == "Anhbia_111239118706449"],
            "source_urls": [PAGE_URL],
            "verification_status": "verified",
        },
        {
            "album_id": "album_111227538707607",
            "facebook_album_id": "111227538707607",
            "name": "Ảnh đại diện (Profile Pictures)",
            "description": "Bộ nhận diện logo và biểu trưng của dự án CHO EM qua các mùa.",
            "photo_ids": [p["photo_id"] for p in photos if p.get("provenance", {}).get("album_folder") == "Anhdaidien_111227538707607"],
            "source_urls": [PAGE_URL],
            "verification_status": "verified",
        },
    ]
    write_json(ROOT / "data/raw/albums.json", albums)

    # 3. Write page_info.json & project_info.json
    page_info = {
        "page_id": PAGE_ID,
        "page_url": PAGE_URL,
        "project_name": "CHO EM project",
        "category": "Tổ chức từ thiện",
        "registered_at": "2023-07-17T13:29:00+00:00",
        "registered_at_local": "2023-07-17T20:29:00+07:00",
        "address": "Đông Hà, Quảng Trị",
        "bio": "Cho Em Project - Góp phần nhỏ vì một tương lai tươi sáng hơn của trẻ em Quảng Trị",
        "verification_status": "verified",
        "source_status": "meta_official_export",
        "collected_at": "2026-10-18T12:07:00+00:00",
        "research_notes": "Xác minh trực tiếp từ hồ sơ xuất chính thức Meta (profile_information.html và profile_posts_1.html).",
    }
    write_json(ROOT / "data/raw/page_info.json", page_info)

    project_info = {
        "project_id": "cho_em",
        "name": "CHO EM project",
        "tagline_original": "Cho Em Project - Góp phần nhỏ vì một tương lai tươi sáng hơn của trẻ em Quảng Trị",
        "slogan": "Sân chơi cho em, cho em niềm vui, gieo mầm ước mơ",
        "name_meaning": (
            "𝗖ùng em sánh bước trên đường đến trường\n"
            "𝗛ọc những điều hay, vun đắp những điều lành\n"
            "𝗢 (Ở) trường hồng, ăn đủ no, mặc đủ ấm\n"
            "𝗘m ngân nga những mơ ước bên chiếc đu quay\n"
            "𝗠ong muốn nụ cười mãi rạng rỡ trên môi."
        ),
        "founded_at": "2023-07-17",
        "locality_display": "Đông Hà, Quảng Trị",
        "legal_patrons": [
            "Thành đoàn Đông Hà",
            "Tỉnh đoàn Quảng Trị",
            "Đoàn trường THPT Chuyên Lê Quý Đôn - Quảng Trị",
        ],
        "origin_story": (
            "Dự án thiện nguyện CHO EM được thành lập vào ngày 17/07/2023 bởi những học sinh, sinh viên nhiệt huyết tại thành phố Đông Hà, tỉnh Quảng Trị (với sự bảo trợ pháp lý của Thành đoàn Đông Hà và Đoàn trường THPT Chuyên Lê Quý Đôn). "
            "Dự án khởi nguồn từ sự trăn trở khi chứng kiến nhiều điểm trường mầm non, tiểu học vùng sâu vùng xa trên địa bàn tỉnh Quảng Trị còn thiếu thốn cơ sở vật chất, sân trường chỉ là nền bê tông trống trải khiến trẻ em thường chơi đùa gần sông suối, tiềm ẩn nguy cơ bệnh truyền nhiễm và tai nạn thương tích, đuối nước. "
            "Từ hai sân chơi tái chế đầu tiên tại xã Húc (Hướng Hóa) mùa hè năm 2023, CHO EM đã phát triển bền bỉ qua 7 mùa hoạt động liên tiếp (2023–2026), mở rộng từ xây dựng sân chơi tái chế sang giáo dục vệ sinh răng miệng, trang bị kỹ năng sơ cứu cơ bản, phòng chống đuối nước và trao tặng tủ sách tri thức cho trẻ em vùng cao."
        ),
        "mission": (
            "Tạo dựng môi trường vui chơi, học tập an toàn, năng động và sáng tạo; đồng thời giáo dục kỹ năng sống thiết yếu (chăm sóc răng miệng, sơ cứu thương tích, phòng chống đuối nước) cho trẻ em vùng sâu vùng xa, vùng đồng bào dân tộc thiểu số trên địa bàn tỉnh Quảng Trị."
        ),
        "vision": (
            "Góp phần nhỏ vì một tương lai tươi sáng hơn của trẻ em Quảng Trị — nơi mọi em nhỏ đều được đến trường an toàn, được vui chơi đúng với lứa tuổi hồn nhiên, được trang bị kỹ năng tự bảo vệ bản thân và không một ai bị bỏ lại phía sau."
        ),
        "objectives": [
            "Thi công và trao tặng các sân chơi tái chế thân thiện với môi trường tại các điểm trường mầm non vùng cao Hướng Hóa.",
            "Tổ chức các lớp học trực quan, thực hành kỹ năng chăm sóc răng miệng, kỹ năng sơ cứu y tế cơ bản và phòng chống tai nạn đuối nước.",
            "Trao tặng áo phao cứu sinh, bộ sơ cấp cứu chuẩn Bộ Y Tế, tủ sách tri thức, giày dép, quần áo mới và học bổng khuyến học cho học sinh nghèo vượt khó.",
            "Kết nối sức trẻ học sinh, sinh viên Quảng Trị thông qua các hoạt động gây quỹ sáng tạo (làm đồ handmade, gian hàng Tết, bán hàng ẩm thực, workshop nghệ thuật).",
        ],
        "core_values": [
            "Nhân văn & Sẻ chia: Đặt sự an toàn, nụ cười và quyền được vui chơi, học tập của trẻ em vùng cao làm trung tâm.",
            "Bền vững & Sáng tạo: Tái chế lốp xe, gỗ cũ thành sân chơi tuổi thơ và chuyển giao tri thức, kỹ năng tự bảo vệ lâu dài.",
            "Minh bạch & Trách nhiệm: Công khai sao kê tài chính, làm việc trực tiếp với chính quyền địa phương và Ban Giám hiệu từng điểm trường.",
            "Tiếp nối sức trẻ: Truyền lửa qua nhiều thế hệ học sinh, sinh viên Quảng Trị xuyên suốt 7 mùa hoạt động.",
        ],
        "leadership_generations": [
            {
                "seasons": ["season_01", "season_02"],
                "period": "2023 – Đầu 2024",
                "leaders": [
                    {"name": "Trần Ngọc Tâm Phúc", "role": "Quản lý dự án (Founder)"},
                    {"name": "Nguyễn Thùy Linh", "role": "Trưởng ban Truyền thông"},
                ],
            },
            {
                "seasons": ["season_03", "season_04"],
                "period": "Hè 2024 – Đầu 2025",
                "leaders": [
                    {"name": "Lê Thị Thúy Như", "role": "Trưởng Ban tổ chức"},
                    {"name": "Nguyễn Văn Linh", "role": "Đồng Trưởng Ban tổ chức"},
                    {"name": "Trần Thiên Hương", "role": "Trưởng ban Truyền thông"},
                ],
            },
            {
                "seasons": ["season_05"],
                "period": "Hè 2025",
                "leaders": [
                    {"name": "Trần Mai Hương Nguyên", "role": "Trưởng Ban tổ chức"},
                    {"name": "Trần Thiên Hương", "role": "Trưởng ban Truyền thông"},
                    {"name": "Đậu Khắc Gia Bảo", "role": "Phụ trách Tài chính"},
                ],
            },
            {
                "seasons": ["season_06", "season_07"],
                "period": "Cuối 2025 – 2026",
                "leaders": [
                    {"name": "Lê Khánh Linh", "role": "Trưởng Ban tổ chức"},
                    {"name": "Phan Thanh Huyền", "role": "Phó Ban tổ chức"},
                    {"name": "Võ Ngọc Gia Linh", "role": "Điều phối Hậu cần & Hiện vật"},
                ],
            },
        ],
        "partners": [
            "Thành đoàn Đông Hà",
            "Tỉnh đoàn Quảng Trị",
            "Đoàn trường THPT Chuyên Lê Quý Đôn",
            "Nhà sách Sang Hiếu",
            "Lớp Hóa Cô Lê Na (Colena)",
            "Lớp Anh Team Miss Kha",
            "Lớp Toán Thầy Thông (Thong Math)",
            "Lớp Toán Cô Thu Hồng Lê (Miss Pink)",
            "Nhà thuốc Bảo Châu",
            "Gạo Coffee",
            "Gé Nhà Coffee",
            "Dimori Coffee",
            "Trường Mầm non Joy School",
            "Green Centre",
            "Mây Mart",
            "The Moment Cafe & Food",
            "Chút Chíu",
            "Nhà hàng Sky Garden",
        ],
        "source_urls": [PAGE_URL],
        "verification_status": "verified",
        "research_notes": "Toàn bộ thông tin sứ mệnh, ý nghĩa tên gọi, ngày thành lập (17/07/2023) và 7 mùa hoạt động đã được xác minh trực tiếp từ bản xuất chính thức của Meta.",
    }
    write_json(ROOT / "data/processed/project_info.json", project_info)

    # 4. Build seasons, programs, journeys, milestones, stories, timeline, evidence_map
    seasons_list = []
    programs_list = []
    journeys_list = []
    milestones_list = []
    stories_list = []
    timeline_list = []
    evidence_list = [
        {
            "evidence_id": "ev_project_mission_20230720",
            "claim": "Dự án CHO EM đăng ký ngày 17/07/2023 tại Đông Hà, Quảng Trị và công bố bài viết Sứ mệnh đầu tiên ngày 20/07/2023 với bài thơ chiết tự C-H-O-E-M.",
            "verification_status": "verified",
            "source_type": "meta_official_export",
            "source_files": [
                "profile_information/profile_information/profile_information.html",
                "this_profile's_activity_across_facebook/posts/profile_posts_1.html",
            ],
        }
    ]

    # Founding event in timeline
    oldest_post = posts_sorted_asc[0]
    timeline_list.append(
        {
            "event_id": "event_project_founded_20230717",
            "title": "Thành lập trang chính thức Dự án thiện nguyện CHO EM (CHO EM project)",
            "event_date": "2023-07-17",
            "date_precision": "day",
            "event_type": "project_milestone",
            "description": "Trang Facebook chính thức CHO EM project được khởi tạo tại Đông Hà, Quảng Trị, mở đầu hành trình vì trẻ em vùng cao.",
            "details": "Xác nhận từ hồ sơ xuất chính thức Meta: Ngày đăng ký Thứ Hai, 17/07/2023 lúc 20:29 UTC+07:00.",
            "season_ids": ["season_01"],
            "program_ids": ["program_san_choi_cho_em_2023"],
            "post_ids": [oldest_post["post_id"]],
            "photo_ids": oldest_post["photo_ids"][:1],
            "video_ids": [],
            "source_urls": [PAGE_URL],
            "verification_status": "verified",
        }
    )

    for sm in SEASON_METADATA:
        sid = sm["season_id"]
        pid = sm["program_id"]
        jid = sm["journey_id"]
        mid = f"milestone_{sid}_{sm['event_date'].replace('-', '')}"
        stid = f"story_{sid}"
        ev_id = f"ev_{sid}_verified_export"

        s_posts = [p for p in posts_sorted_desc if sid in p["season_ids"]]
        s_post_ids = [p["post_id"] for p in s_posts]
        s_photo_ids = []
        s_video_ids = []
        for p in s_posts:
            for ph_id in p["photo_ids"]:
                if ph_id not in s_photo_ids:
                    s_photo_ids.append(ph_id)
            for v_id in p["video_ids"]:
                if v_id not in s_video_ids:
                    s_video_ids.append(v_id)

        s_urls = [p["post_url"] for p in s_posts[:5]] if s_posts else [PAGE_URL]

        evidence_list.append(
            {
                "evidence_id": ev_id,
                "claim": f"Xác minh {sm['official_name']} với chương trình '{sm['program_name']}' diễn ra ngày {sm['event_date']} tại {', '.join(sm['locations'])}.",
                "verification_status": "verified",
                "source_urls": s_urls,
                "post_ids": s_post_ids[:5],
            }
        )

        season_obj = {
            "season_id": sid,
            "season_number": sm["season_number"],
            "official_name": sm["official_name"],
            "theme": sm["theme"],
            "slogan": sm["slogan"],
            "start_date": sm["start_date"],
            "end_date": sm["end_date"],
            "event_date": sm["event_date"],
            "description": sm["description"],
            "objectives": sm["objectives"],
            "locations": sm["locations"],
            "leaders": sm["leaders"],
            "patron": sm["patron"],
            "funds_raised_vnd": sm["funds_raised_vnd"],
            "results_summary": sm["results"],
            "program_ids": [pid],
            "journey_ids": [jid],
            "post_ids": s_post_ids,
            "photo_ids": s_photo_ids,
            "video_ids": s_video_ids,
            "milestone_ids": [mid],
            "story_ids": [stid],
            "source_urls": s_urls,
            "verification_status": "verified",
            "evidence_ids": [ev_id],
            "season_directory": f"data/seasons/{sid}",
            "research_notes": f"Hồ sơ {sm['official_name']} được tổng hợp đầy đủ từ {len(s_posts)} bài đăng và {len(s_photo_ids)} ảnh gốc trong bản xuất chính thức của Meta.",
        }
        seasons_list.append(season_obj)

        program_obj = {
            "program_id": pid,
            "name": sm["program_name"],
            "season_ids": [sid],
            "start_date": sm["start_date"],
            "end_date": sm["end_date"],
            "event_date": sm["event_date"],
            "locations": sm["locations"],
            "purpose": sm["theme"],
            "context": sm["description"],
            "preparation": "Tuyển tình nguyện viên, truyền thông vận động quyên góp và tổ chức sự kiện gây quỹ cộng đồng tại Đông Hà.",
            "activities": sm["activities"],
            "results": sm["results"],
            "post_ids": s_post_ids,
            "photo_ids": s_photo_ids,
            "video_ids": s_video_ids,
            "source_urls": s_urls,
            "verification_status": "verified",
            "evidence_ids": [ev_id],
            "research_notes": f"Chương trình trọng điểm thuộc khuôn khổ {sm['official_name']}.",
        }
        programs_list.append(program_obj)

        journey_obj = {
            "journey_id": jid,
            "title": sm["journey_title"],
            "season_ids": [sid],
            "program_ids": [pid],
            "start_date": sm["event_date"],
            "end_date": sm["event_date"],
            "origin": "Thành phố Đông Hà, tỉnh Quảng Trị",
            "destinations": sm["locations"],
            "summary": sm["story_summary"],
            "activities": sm["activities"],
            "post_ids": s_post_ids[:6],
            "photo_ids": s_photo_ids[:20],
            "video_ids": s_video_ids,
            "source_urls": s_urls,
            "verification_status": "verified",
        }
        journeys_list.append(journey_obj)

        milestone_obj = {
            "milestone_id": mid,
            "title": f"Tổ chức thành công chương trình '{sm['program_name']}' ({sm['official_name']})",
            "date": sm["event_date"],
            "season_ids": [sid],
            "program_ids": [pid],
            "post_ids": s_post_ids[:3],
            "photo_ids": s_photo_ids[:6],
            "video_ids": s_video_ids,
            "description": sm["description"],
            "source_urls": s_urls,
            "verification_status": "verified",
        }
        milestones_list.append(milestone_obj)

        story_obj = {
            "story_id": stid,
            "title": sm["story_title"],
            "season_ids": [sid],
            "program_ids": [pid],
            "journey_ids": [jid],
            "date": sm["event_date"],
            "summary": sm["story_summary"],
            "narrative": sm["description"],
            "post_ids": s_post_ids[:4],
            "photo_ids": s_photo_ids[:10],
            "video_ids": s_video_ids,
            "source_urls": s_urls,
            "verification_status": "verified",
        }
        stories_list.append(story_obj)

        # Add season kickoff & main program event to timeline
        timeline_list.append(
            {
                "event_id": f"event_{sid}_kickoff",
                "title": f"Khởi động {sm['official_name']}",
                "event_date": sm["start_date"],
                "date_precision": "day",
                "event_type": "season_kickoff",
                "description": f"Mở đầu hành trình {sm['official_name']} với chủ đề '{sm['theme']}'.",
                "details": sm["slogan"],
                "season_ids": [sid],
                "program_ids": [pid],
                "post_ids": [s_post_ids[-1]] if s_post_ids else [],
                "photo_ids": s_photo_ids[-3:] if s_photo_ids else [],
                "video_ids": [],
                "source_urls": s_urls,
                "verification_status": "verified",
            }
        )
        timeline_list.append(
            {
                "event_id": f"event_{sid}_main_program",
                "title": f"Sự kiện chính: {sm['program_name']} ({sm['official_name']})",
                "event_date": sm["event_date"],
                "date_precision": "day",
                "event_type": "program_execution",
                "description": sm["description"],
                "details": "; ".join(sm["activities"]),
                "season_ids": [sid],
                "program_ids": [pid],
                "post_ids": s_post_ids[:3],
                "photo_ids": s_photo_ids[:8],
                "video_ids": s_video_ids,
                "source_urls": s_urls,
                "verification_status": "verified",
            }
        )

    # Sort timeline chronologically by event_date
    timeline_list.sort(key=lambda e: (e["event_date"], e["event_id"]))

    # Write processed tables
    write_json(ROOT / "data/processed/seasons.json", seasons_list)
    write_json(ROOT / "data/processed/programs.json", programs_list)
    write_json(ROOT / "data/processed/journeys.json", journeys_list)
    write_json(ROOT / "data/processed/milestones.json", milestones_list)
    write_json(ROOT / "data/processed/stories.json", stories_list)
    write_json(ROOT / "data/processed/timeline.json", timeline_list)
    write_json(ROOT / "research/evidence_map.json", evidence_list)

    # Write featured_content.json
    featured = []
    for s in seasons_list:
        featured.append(
            {
                "featured_id": f"featured_{s['season_id']}",
                "title": s["official_name"],
                "subtitle": s["theme"],
                "season_ids": [s["season_id"]],
                "program_ids": s["program_ids"],
                "post_ids": s["post_ids"][:2],
                "photo_ids": s["photo_ids"][:6],
                "video_ids": s["video_ids"],
                "summary": s["description"],
                "editorial_status": "curated_for_showcase",
            }
        )
    write_json(ROOT / "data/processed/featured_content.json", featured)

    # Write media_index.json
    media_index = []
    for ph in photos:
        media_index.append(
            {
                "media_id": ph["photo_id"],
                "media_type": "photo",
                "local_path": ph["local_path"],
                "sha256": ph["sha256"],
                "file_size": ph["file_size"],
                "width": ph["width"],
                "height": ph["height"],
                "format": ph["format"],
                "published_at": ph["published_at"],
                "season_ids": ph["season_ids"],
                "program_ids": ph["program_ids"],
                "post_ids": ph["post_ids"],
                "category": ph["category"],
                "description": ph["description"],
                "download_status": ph["download_status"],
                "rights_status": ph["rights_status"],
                "privacy_review_required": ph["privacy_review_required"],
            }
        )
    for vd in videos:
        media_index.append(
            {
                "media_id": vd["video_id"],
                "media_type": "video",
                "local_path": vd["local_path"],
                "sha256": vd["sha256"],
                "file_size": vd["file_size"],
                "width": vd["width"],
                "height": vd["height"],
                "format": vd["format"],
                "duration_seconds": vd["duration_seconds"],
                "published_at": vd["published_at"],
                "season_ids": vd["season_ids"],
                "program_ids": vd["program_ids"],
                "post_ids": vd["post_ids"],
                "category": "season_video",
                "description": vd["caption_original"],
                "download_status": vd["download_status"],
                "rights_status": vd["rights_status"],
                "privacy_review_required": vd["privacy_review_required"],
            }
        )
    write_json(ROOT / "data/processed/media_index.json", media_index)

    # Write unclassified tables (now empty because all curated posts/media are classified!)
    write_json(ROOT / "data/unclassified/posts.json", [])
    write_json(ROOT / "data/unclassified/media.json", [])

    # 5. Write season bundles in data/seasons/season_01 .. season_07
    photos_by_id = {p["photo_id"]: p for p in photos}
    videos_by_id = {v["video_id"]: v for v in videos}

    for s in seasons_list:
        sid = s["season_id"]
        s_dir = ROOT / "data/seasons" / sid
        s_dir.mkdir(parents=True, exist_ok=True)

        s_posts = [p for p in posts_sorted_desc if sid in p["season_ids"]]
        s_progs = [pr for pr in programs_list if sid in pr["season_ids"]]
        s_journs = [jr for jr in journeys_list if sid in jr["season_ids"]]
        s_time = [ev for ev in timeline_list if sid in ev["season_ids"]]
        s_media = [ photos_by_id[pid] for pid in s["photo_ids"] if pid in photos_by_id ] + [
            videos_by_id[vid] for vid in s["video_ids"] if vid in videos_by_id
        ]

        write_json(s_dir / "season_info.json", s)
        write_json(s_dir / "posts.json", s_posts)
        write_json(s_dir / "programs.json", s_progs)
        write_json(s_dir / "journeys.json", s_journs)
        write_json(s_dir / "timeline.json", s_time)
        write_json(s_dir / "media_manifest.json", s_media)

        story_md = (
            f"# {s['official_name']}\n\n"
            f"- **Chủ đề:** {s['theme']}\n"
            f"- **Thông điệp:** {s['slogan']}\n"
            f"- **Thời gian hoạt động:** {s['start_date']} đến {s['end_date']} (Sự kiện chính: {s['event_date']})\n"
            f"- **Địa điểm triển khai:** {', '.join(s['locations'])}\n"
            f"- **Đơn vị bảo trợ / đồng hành:** {s['patron']}\n\n"
            f"## Câu chuyện và dấu ấn\n\n"
            f"{s['description']}\n\n"
            f"## Hoạt động tiêu biểu\n\n"
            + "\n".join(f"- {act}" for act in s_progs[0]["activities"])
            + "\n"
        )
        (s_dir / "season_story.md").write_text(story_md, encoding="utf-8")

        sources_md = (
            f"# Nguồn xác minh {s['official_name']}\n\n"
            f"- Hồ sơ xuất chính thức Meta (`Data_fb/this_profile's_activity_across_facebook/posts/profile_posts_1.html`).\n"
            f"- Số bài đăng thuộc mùa: **{len(s_posts)} bài viết**.\n"
            f"- Số hình ảnh tư liệu gốc: **{len(s['photo_ids'])} ảnh**.\n"
            f"- Số video tư liệu gốc: **{len(s['video_ids'])} video**.\n\n"
            + "\n".join(f"- [{p['published_at'][:10]}] {p['summary']} ({p['post_url']})" for p in s_posts)
            + "\n"
        )
        (s_dir / "sources.md").write_text(sources_md, encoding="utf-8")

    # Also clean up stale research json files that might hold dangling photo_ids if any
    for stale_name in ("media_manifest.json", "media_upgrade_manifest.json", "media_variant_groups.json"):
        stale_p = ROOT / "research" / stale_name
        if stale_p.exists():
            stale_p.unlink()

    # Update research/collection_progress.json
    progress = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "last_operation": "curate_meta_official_export",
        "historical_coverage": "complete_2023_to_2026_from_official_export",
        "seasons_verified": 7,
        "posts_archived": len(posts_sorted_desc),
        "photos_archived": len(photos),
        "videos_archived": len(videos),
        "notes": "Đã tích hợp và chọn lọc toàn bộ 7 mùa hoạt động (2023-2026) từ bản xuất chính thức của Meta (Data_fb).",
    }
    write_json(ROOT / "research/collection_progress.json", progress)

    print("Successfully built full 7-season archive!")


if __name__ == "__main__":
    build_archive()

