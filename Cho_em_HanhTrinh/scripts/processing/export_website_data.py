#!/usr/bin/env python3
"""Generate website/data/archive_bundle.js with full Unicode normalization,
natural Vietnamese sentence-case/uppercase typography, smart quote formatting,
post categorization, and curated action photos."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"D:\CHO_EM\Cho_em_HanhTrinh")

# Curated, visually distinct field-action hero photos for each season
CURATED_SEASON_HERO_PHOTOS = {
    "season_01": "assets/originals/images/e8b97e275521d0d231ce22f6fae7df84db72860e9b1b00698cb034c73e06101f.jpg",
    "season_02": "assets/originals/images/6d6788f02cb7212fb85b92ab8f76f946f8ca2764426006044b07993e91e19812.jpg",
    "season_03": "assets/originals/images/d9445fe053b236a7c0572b736d7303168838a5eeb5f553dee04675910a22b4e9.jpg",
    "season_04": "assets/originals/images/31cf728b3219196b2a18f64f00310328678521cfbde39cd6879d8e00e9d5df00.jpg",
    "season_05": "assets/originals/images/1a8a1294e364cbccd2d08ed716c2fc79db67a0804fe1e09dd8e596caf8d5d358.jpg",
    "season_06": "assets/originals/images/11da218aa720f14ac2481d2e9d2436713def29ab87ffe249dba49de4661f5567.jpg",
    "season_07": "assets/originals/images/fef45178deab58dc7729d1af94ed83c84197ef55534c7503401a737bdeb8d2c8.jpg",
}

# Natural Vietnamese typography overrides (eliminating English Every-Word Title Case)
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


def normalize_smart_quotes(text: str) -> str:
    """Convert straight double/single quotes around phrases into typographic “...” quotes
    and replace English Title-Cased campaign phrases with natural Vietnamese sentence case."""
    if not text:
        return ""
    for old_phrase, new_phrase in TITLE_CASE_PHRASE_FIXES:
        text = text.replace(old_phrase, new_phrase)
    # Replace straight double quotes "phrase" with “phrase”
    text = re.sub(r'"([^"\n]{1,120})"', r"“\1”", text)
    # Replace single quotes 'phrase' (when not inside words) with “phrase”
    text = re.sub(r"(?<!\w)'([^'\n]{2,120})'(?!\w)", r"“\1”", text)
    # Collapse nested double smart quotes ““...”” -> “...”
    text = re.sub(r"“+([^”]+)”+", r"“\1”", text)
    return text


def normalize_vn_text(text: str | None) -> str:
    """Convert Mathematical Alphanumeric Unicode (𝐂𝐇𝐎 𝐄𝐌) and combining marks
    into clean, standard NFC Vietnamese UTF-8 text."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = re.sub(r"[\u200b\u200c\u200d\ufeff\ufe0e\ufe0f]", "", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalize_smart_quotes(normalized.strip())


def clean_post_title(raw_caption: str, fallback_summary: str) -> str:
    """Extract a clean Vietnamese headline from a post caption (ALL CAPS for post headers)."""
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

    first_line = normalize_smart_quotes(first_line)

    if not first_line:
        first_line = normalize_vn_text(fallback_summary)

    # Ensure post headlines are consistently UPPERCASE (standard Vietnamese editorial header style)
    return first_line.upper()


def split_body_and_footer(raw_caption: str) -> tuple[str, list[str]]:
    """Separate the main narrative body from the repetitive contact footer and hashtags."""
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
    """Classify a post into a clear, reader-friendly Vietnamese category."""
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

    # Normalize timeline titles and descriptions
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

    # Pre-process posts to get clean titles and bodies
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

        # Build resolved photos with rich contextual descriptions
        resolved_photos = []
        for p in s_photos:
            raw_desc = normalize_vn_text(p.get("description", ""))
            parent_pid = p["post_ids"][0] if p.get("post_ids") else None
            parent_clean = cleaned_posts_map.get(parent_pid, {})
            parent_title = parent_clean.get("title_clean") or s["official_name"].upper()
            parent_body = parent_clean.get("body_clean") or s["description"]

            is_generic = (
                not raw_desc
                or raw_desc.lower() in {"ảnh", "tải lên từ di động", "ảnh trên dòng thời gian"}
                or raw_desc.startswith("Ảnh tư liệu chính thức từ trang CHO EM")
            )
            caption_clean = parent_body if is_generic else raw_desc
            short_title = parent_title if is_generic else clean_post_title(raw_desc, parent_title)

            resolved_photos.append(
                {
                    "photo_id": p["photo_id"],
                    "local_path": p["local_path"],
                    "width": p["width"] or 960,
                    "height": p["height"] or 720,
                    "published_at": p["published_at"],
                    "title_clean": short_title,
                    "description": caption_clean,
                    "category_id": parent_clean.get("category_id", "recap"),
                    "category_label": parent_clean.get("category_label", "Hình ảnh chuyến đi"),
                    "post_id": parent_pid,
                }
            )

        def photo_sort_key(item):
            is_hero = 0 if item["local_path"] == hero_photo else 1
            cat_rank = CATEGORY_PRIORITY.get(item["category_id"], 3)
            return (is_hero, cat_rank)

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
                    "photo_paths": [
                        photos_by_id[ph_id]["local_path"]
                        for ph_id in p["photo_ids"]
                        if ph_id in photos_by_id
                    ],
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
        "generated_at": "2026-11-09T09:46:00+07:00",
        "project_info": project_info,
        "page_info": page_info,
        "stats": {
            "total_seasons": len(seasons),
            "total_posts": len(posts),
            "total_photos": len(photos),
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
