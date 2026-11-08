#!/usr/bin/env python3
"""Generate website/data/archive_bundle.js with full Unicode normalization,
clean Vietnamese titles/excerpts, post categorization, and curated action photos."""

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


def normalize_vn_text(text: str | None) -> str:
    """Convert Mathematical Alphanumeric Unicode (𝐂𝐇𝐎 𝐄𝐌) and combining marks
    into clean, standard NFC Vietnamese UTF-8 text."""
    if not text:
        return ""
    # NFKC converts mathematical bold/italic/sans-serif symbols to regular ASCII/Latin
    normalized = unicodedata.normalize("NFKC", text)
    # NFC composes base letters + combining Vietnamese tone/vowel marks into single glyphs
    normalized = unicodedata.normalize("NFC", normalized)
    # Remove zero-width joiners/spaces and variation selectors that break web fonts
    normalized = re.sub(r"[\u200b\u200c\u200d\ufeff\ufe0e\ufe0f]", "", normalized)
    # Normalize multiple spaces on the same line
    normalized = re.sub(r"[ \t]+", " ", normalized)
    # Normalize 3+ newlines to 2 newlines
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def clean_post_title(raw_caption: str, fallback_summary: str) -> str:
    """Extract a clean, human-readable Vietnamese headline from a post caption."""
    norm_cap = normalize_vn_text(raw_caption)
    lines = [ln.strip() for ln in norm_cap.splitlines() if ln.strip()]
    first_line = lines[0] if lines else normalize_vn_text(fallback_summary)

    # Strip surrounding brackets/pipes like |...| or [...]
    first_line = re.sub(r"^[\|\[\]【】\s]+|[\|\[\]【】\s]+$", "", first_line)
    # Strip leading decorative emojis/symbols
    first_line = re.sub(r"^[^\wÀ-ỹ\"“”‘’\(\)]+", "", first_line).strip()
    # Strip trailing decorative emojis
    first_line = re.sub(r"[^\wÀ-ỹ\"“”‘’\.\!\?\)\]]+$", "", first_line).strip()

    # Standardize "CHO EM:" or "CHO EM |" prefix
    first_line = re.sub(r"^CHO\s+EM\s*[:\|\-–—]\s*", "", first_line, flags=re.IGNORECASE).strip()
    first_line = re.sub(r"^NEWS\s*[:\|\-–—]\s*", "", first_line, flags=re.IGNORECASE).strip()

    # Balance unclosed smart/straight quotes
    if first_line.count("“") > first_line.count("”"):
        first_line += "”"
    if first_line.count('"') % 2 == 1:
        first_line += '"'

    if not first_line:
        first_line = normalize_vn_text(fallback_summary)

    # Convert ALL-CAPS shouting titles into readable Vietnamese sentence/title case
    # while keeping proper nouns, acronyms, and quoted program names intact
    return first_line


def split_body_and_footer(raw_caption: str) -> tuple[str, list[str]]:
    """Separate the main narrative body from the repetitive contact footer and hashtags."""
    norm = normalize_vn_text(raw_caption)
    hashtags = re.findall(r"#[A-Za-z0-9_À-ỹ]+", norm)

    lines = norm.splitlines()
    # Skip the first line if it's a bracketed/piped title line
    body_lines = lines[1:] if len(lines) > 1 else lines

    cleaned_lines = []
    for ln in body_lines:
        s = ln.strip()
        if not s:
            cleaned_lines.append("")
            continue
        # Stop before the repetitive contact separator block
        if re.match(r"^[_\-─━═\*]{5,}$", s):
            break
        if re.match(r"^(Mọi thông tin chi tiết|Thông tin liên hệ|Liên hệ với chúng mình)", s, flags=re.IGNORECASE):
            break
        # Skip pure hashtag lines
        if re.match(r"^(#[A-Za-z0-9_À-ỹ]+\s*)+$", s):
            continue
        cleaned_lines.append(s)

    body_clean = "\n".join(cleaned_lines).strip()
    body_clean = re.sub(r"\n{3,}", "\n\n", body_clean)
    if not body_clean:
        body_clean = norm
    return body_clean, hashtags


def classify_post(title_clean: str, body_clean: str) -> tuple[str, str]:
    """Classify a post into a logical editorial category."""
    upper = (title_clean + " " + body_clean[:200]).upper()
    if any(k in upper for k in ["NHÀ TÀI TRỢ", "ĐƠN VỊ ĐỒNG HÀNH", "TRI ÂN NHÀ TÀI TRỢ", "CẢM ƠN NHÀ TÀI TRỢ", "BẢO TRỢ"]):
        return "sponsor", "Tri ân Nhà tài trợ"
    if any(k in upper for k in ["TỔNG KẾT", "RECAP CHƯƠNG TRÌNH", "VIDEO RECAP", "CHUYẾN ĐI CHO EM", "NHỮNG KHOẢNH KHẮC QUÝ GIÁ", "NHÌN LẠI HÀNH TRÌNH", "RECAP 2025", "LỄ KHÁNH THÀNH"]):
        return "recap", "Tổng kết & Ký sự"
    if any(k in upper for k in ["TUYỂN THÀNH VIÊN", "TUYỂN QUÂN", "CORE TEAM", "BAN TỔ CHỨC", "PHỎNG VẤN", "ỨNG VIÊN", "ĐƠN ĐĂNG KÝ", "GIA ĐÌNH CHO EM"]):
        return "team", "Ban Tổ Chức & Nhân sự"
    if any(k in upper for k in ["SƠ CỨU", "ĐUỐI NƯỚC", "RĂNG MIỆNG", "CẨM NANG", "KỸ NĂNG", "MINIGAME", "GIẢI Ô CHỮ"]):
        return "knowledge", "Kiến thức & Kỹ năng"
    return "campaign", "Phát động & Gây quỹ"


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
    posts_by_id = {p["post_id"]: p for p in posts}

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
        s_posts = [p for p in posts if sid in p.get("season_ids", [])]
        s_photos = [photos_by_id[pid] for pid in s["photo_ids"] if pid in photos_by_id]
        s_videos = [videos_by_id[vid] for vid in s["video_ids"] if vid in videos_by_id]
        s_prog = programs_by_id.get(s["program_ids"][0]) if s.get("program_ids") else None
        s_story = stories_by_id.get(s["story_ids"][0]) if s.get("story_ids") else None

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
        for idx, p in enumerate(s_photos):
            raw_desc = normalize_vn_text(p.get("description", ""))
            parent_pid = p["post_ids"][0] if p.get("post_ids") else None
            parent_clean = cleaned_posts_map.get(parent_pid, {})
            parent_title = parent_clean.get("title_clean") or s["official_name"]
            parent_body = parent_clean.get("body_clean") or s["description"]

            is_generic = (
                not raw_desc
                or raw_desc.lower() in {"ảnh", "tải lên từ di động", "ảnh trên dòng thời gian"}
                or raw_desc.startswith("Ảnh tư liệu chính thức từ trang CHO EM")
            )
            caption_clean = parent_body if is_generic else raw_desc
            short_title = parent_title if is_generic else (raw_desc.splitlines()[0][:95])

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
                    "category_label": parent_clean.get("category_label", "Tư liệu mùa"),
                    "post_id": parent_pid,
                }
            )

        # Reorder season photos so curated hero photo and recap photos appear first!
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

        # Sort posts so Recap & Campaign posts appear before Sponsor posts by default
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
        "generated_at": "2026-11-07T13:52:00+07:00",
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
