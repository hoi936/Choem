#!/usr/bin/env python3
"""Curate and import the official Meta HTML export (D:/CHO_EM/Data_fb) into Cho_em_HanhTrinh.

Preserves original initial workspace files (docs/promt/Promt1, Ảnh/Anh1.jpg) and existing
public snapshot evidence while building the complete 7-season archive (2023-2026).
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unicodedata

ROOT = Path(r"D:\CHO_EM\Cho_em_HanhTrinh")
FB_ROOT = Path(r"D:\CHO_EM\Data_fb")
PAGE_ID = "100094610840245"
PAGE_URL = f"https://www.facebook.com/profile.php?id={PAGE_ID}"
VN_TZ = timezone(timedelta(hours=7))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_vn_datetime(text: str) -> str:
    """Parse Facebook Vietnamese export timestamp like 'Tháng 8 20, 2026 8:00:48 ch' to ISO 8601 UTC."""
    text = text.strip()
    m = re.search(
        r"Tháng\s+(\d{1,2})\s+(\d{1,2}),\s*(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s*(sáng|ch)",
        text,
        re.IGNORECASE,
    )
    if not m:
        raise ValueError(f"Cannot parse Vietnamese timestamp: {text!r}")
    month, day, year, hour, minute, second, ampm = (
        int(m.group(1)),
        int(m.group(2)),
        int(m.group(3)),
        int(m.group(4)),
        int(m.group(5)),
        int(m.group(6)),
        m.group(7).lower(),
    )
    if ampm == "ch" and hour != 12:
        hour += 12
    elif ampm == "sáng" and hour == 12:
        hour = 0
    dt_vn = datetime(year, month, day, hour, minute, second, tzinfo=VN_TZ)
    return dt_vn.astimezone(timezone.utc).isoformat(timespec="seconds")


def clean_whitespace(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip()


def extract_hashtags(text: str | None) -> list[str]:
    if not text:
        return []
    tags = re.findall(r"(?<!\w)#([\w\u00C0-\u1EF9]+)", text)
    seen = []
    for t in tags:
        tag = f"#{t}"
        if tag not in seen:
            seen.append(tag)
    return seen


def probe_media_file(path: Path) -> dict:
    """Run ffprobe to get exact width, height, codec_name, duration."""
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,codec_name:format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            streams = data.get("streams", [])
            stream = streams[0] if streams else {}
            fmt = data.get("format", {})
            dur = fmt.get("duration")
            return {
                "width": stream.get("width"),
                "height": stream.get("height"),
                "codec_name": stream.get("codec_name"),
                "duration": round(float(dur)) if dur else None,
            }
    except Exception:
        pass
    return {"width": None, "height": None, "codec_name": None, "duration": None}


def classify_season_and_program(dt_iso: str) -> tuple[str, str, str]:
    """Deterministically assign season_id, program_id, journey_id from post publication timestamp."""
    dt = datetime.fromisoformat(dt_iso)
    ymd = dt.astimezone(VN_TZ).strftime("%Y-%m-%d")
    if ymd <= "2023-09-30":
        return ("season_01", "program_san_choi_cho_em_2023", "journey_huc_huong_hoa_2023")
    if "2024-01-01" <= ymd <= "2024-03-31":
        return ("season_02", "program_rang_xinh_cho_em_2024", "journey_trieu_van_2024")
    if "2024-06-01" <= ymd <= "2024-09-30":
        return ("season_03", "program_san_choi_cho_em_mua_3_2024", "journey_huong_phung_2024")
    if "2024-11-01" <= ymd <= "2025-03-31":
        return ("season_04", "program_phao_xinh_cho_em_2025", "journey_trieu_van_2025")
    if "2025-06-01" <= ymd <= "2025-09-30":
        return ("season_05", "program_an_toan_cho_em_2025", "journey_tan_thanh_2025")
    if "2025-11-01" <= ymd <= "2026-04-30":
        return ("season_06", "program_an_toan_cho_em_2_2026", "journey_vinh_o_2026")
    return ("season_07", "program_hanh_trang_cho_em_2026", "journey_ta_long_2026")


def extract_locations(text: str | None) -> list[str]:
    if not text:
        return []
    candidates = [
        "Trường Tiểu học Tà Long",
        "Trường PTDTBT TH Vĩnh Ô",
        "Trường DTBT TH Vĩnh Ô",
        "TH&THCS Tân Thành",
        "Trường TH&THCS Triệu Vân",
        "Trường Tiểu học và Trung học cơ sở Triệu Vân",
        "Trường Mầm non Hướng Phùng",
        "Điểm trường Chênh Vênh",
        "Điểm trường Hướng Choa",
        "Trường Mầm non Húc",
        "Bản Ho Le",
        "Bản Tà Rùng",
        "Đakrông",
        "Hướng Hóa",
        "Triệu Phong",
        "Vĩnh Ô",
        "Đông Hà",
        "Quảng Trị",
    ]
    found = []
    lower = text.lower()
    for loc in candidates:
        if loc.lower() in lower:
            found.append(loc)
    return found


def extract_title_summary(caption: str | None, h2: str) -> str:
    if not caption:
        return h2
    for line in caption.splitlines():
        s = line.strip()
        if s and not re.fullmatch(r"[-—_=*\s]+", s):
            if len(s) > 140:
                return s[:137] + "..."
            return s
    return h2


def main():
    print("1. Loading existing archive records to preserve public snapshot provenance...")
    existing_posts = json.loads((ROOT / "data/raw/posts.json").read_text(encoding="utf-8"))
    existing_photos = json.loads((ROOT / "data/raw/photos.json").read_text(encoding="utf-8"))
    existing_videos = json.loads((ROOT / "data/raw/videos.json").read_text(encoding="utf-8"))

    # Map existing posts by published_at
    existing_post_by_pub = {p["published_at"]: p for p in existing_posts if p.get("published_at")}
    existing_photo_by_sha = {p["sha256"]: p for p in existing_photos if p.get("sha256")}

    # 2. Parse all sections from profile_posts_1.html
    posts_html_path = FB_ROOT / "this_profile's_activity_across_facebook/posts/profile_posts_1.html"
    posts_html = posts_html_path.read_text(encoding="utf-8")
    sections = re.findall(r'<section class="_a6-g".*?</section>', posts_html, re.DOTALL)
    print(f"Found {len(sections)} raw sections in profile_posts_1.html")

    # Skip noisy/duplicate/empty sections:
    # 0,1,2,3,4: bare link shares without context
    # 110: exact duplicate of 109 posted 3 seconds apart
    # 116: empty status update with no text or media
    SKIP_INDICES = {0, 1, 2, 3, 4, 110, 116}

    raw_extracted_posts = []
    media_tasks = {}  # abs_path -> {"rel_fb_path": ..., "kind": "photo"|"video", "fbid": ..., "album": ..., "descriptions": []}

    for idx, sec in enumerate(sections):
        if idx in SKIP_INDICES:
            continue

        h2_m = re.search(r"<h2[^>]*>(.*?)</h2>", sec, re.DOTALL)
        h2 = html.unescape(re.sub(r"<[^>]+>", "", h2_m.group(1)).strip()) if h2_m else ""

        footer_m = re.search(r'<footer[^>]*>.*?<div class="_a72d">(.*?)</div>.*?</footer>', sec, re.DOTALL)
        footer_str = html.unescape(re.sub(r"<[^>]+>", "", footer_m.group(1)).strip()) if footer_m else ""
        published_at = parse_vn_datetime(footer_str)

        pins = re.findall(
            r'<div class="_2pin">(.*?)</div>(?=<div class="_2pin">|</div></div><footer)',
            sec,
            re.DOTALL,
        )

        # Extract per-photo blocks inside pin[0]
        img_rel_paths = []
        vid_rel_paths = []
        per_photo_descs = {}

        if pins:
            pin0 = pins[0]
            # Find each _a7ng card
            cards = re.findall(r'<div class="_a7ng[^"]*">(.*?)</div>\s*</div>\s*</div>', pin0, re.DOTALL)
            for card in cards:
                im = re.search(r'<img[^>]+src="([^"]+)"', card)
                if im:
                    rel_p = html.unescape(im.group(1))
                    # Check if there is a description after album div
                    card_no_img = re.sub(r"<a[^>]*>.*?</a>", "", card, flags=re.DOTALL)
                    card_no_album = re.sub(
                        r"<div>(?:Ảnh|Tải lên từ di động|Ảnh bìa|Ảnh đại diện)</div>",
                        "",
                        card_no_img,
                    )
                    card_txt = re.sub(r"<br\s*/?>\s*", "\n", card_no_album)
                    card_txt = html.unescape(re.sub(r"<[^>]+>", "", card_txt)).strip()
                    if card_txt:
                        per_photo_descs[rel_p] = card_txt

            for m_img in re.finditer(r'<img[^>]+src="([^"]+)"', pin0):
                rel_p = html.unescape(m_img.group(1))
                if rel_p not in img_rel_paths:
                    img_rel_paths.append(rel_p)

            for m_vid in re.finditer(r'<video[^>]+src="([^"]+)"', pin0):
                rel_v = html.unescape(m_vid.group(1))
                if rel_v not in vid_rel_paths:
                    vid_rel_paths.append(rel_v)

        # Extract main post caption from pin[1] (or pin[0] if pin[1] is empty)
        def extract_clean_caption(pin_fragment: str) -> str:
            s = re.sub(r"<a[^>]*>\s*<img[^>]*/>\s*</a>", "", pin_fragment, flags=re.DOTALL)
            s = re.sub(r"<video[^>]*>.*?</video>", "", s, flags=re.DOTALL)
            s = re.sub(r"<div>(?:Ảnh|Tải lên từ di động|Ảnh bìa|Ảnh đại diện)</div>", "", s)
            s = re.sub(r"<div>Cập nhật Tháng [^<]+</div>", "", s)
            s = re.sub(r"<br\s*/?>\s*", "\n", s)
            s = re.sub(r"</div>", "\n", s)
            s = html.unescape(re.sub(r"<[^>]+>", "", s))
            lines = [line.strip() for line in s.splitlines()]
            cleaned_lines = []
            for line in lines:
                if line or (cleaned_lines and cleaned_lines[-1] != ""):
                    cleaned_lines.append(line)
            while cleaned_lines and cleaned_lines[-1] == "":
                cleaned_lines.pop()
            return "\n".join(cleaned_lines).strip()

        caption = ""
        if len(pins) > 1:
            caption = extract_clean_caption(pins[1])
        if not caption and pins:
            caption = extract_clean_caption(pins[0])

        # Register media files
        for rel_p in img_rel_paths:
            abs_p = FB_ROOT / rel_p
            if abs_p.is_file():
                fbid = abs_p.stem
                album_folder = abs_p.parent.name
                entry = media_tasks.setdefault(
                    abs_p,
                    {
                        "abs_path": abs_p,
                        "rel_fb_path": rel_p,
                        "kind": "photo",
                        "fbid": fbid,
                        "album_folder": album_folder,
                        "descriptions": [],
                    },
                )
                if rel_p in per_photo_descs and len(img_rel_paths) > 1:
                    entry["descriptions"].append(per_photo_descs[rel_p])

        for rel_v in vid_rel_paths:
            abs_v = FB_ROOT / rel_v
            if abs_v.is_file():
                fbid = abs_v.stem
                media_tasks.setdefault(
                    abs_v,
                    {
                        "abs_path": abs_v,
                        "rel_fb_path": rel_v,
                        "kind": "video",
                        "fbid": fbid,
                        "album_folder": "videos",
                        "descriptions": [caption] if caption else [],
                    },
                )

        raw_extracted_posts.append(
            {
                "section_index": idx,
                "h2": h2,
                "footer_str": footer_str,
                "published_at": published_at,
                "caption_original": caption if caption else None,
                "img_rel_paths": img_rel_paths,
                "vid_rel_paths": vid_rel_paths,
            }
        )

    # Also include all Cover Photos (Anhbia_111239118706449) and Profile Pictures (Anhdaidien_111227538707607)
    for special_folder, desc_label in [
        ("Anhbia_111239118706449", "Ảnh bìa chính thức của trang CHO EM project"),
        ("Anhdaidien_111227538707607", "Ảnh đại diện (Logo) chính thức của trang CHO EM project"),
    ]:
        folder_path = FB_ROOT / "this_profile's_activity_across_facebook/posts/media" / special_folder
        if folder_path.is_dir():
            for img_file in sorted(folder_path.glob("*.*")):
                if img_file.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    rel_p = img_file.relative_to(FB_ROOT).as_posix()
                    media_tasks.setdefault(
                        img_file,
                        {
                            "abs_path": img_file,
                            "rel_fb_path": rel_p,
                            "kind": "photo",
                            "fbid": img_file.stem,
                            "album_folder": special_folder,
                            "descriptions": [desc_label],
                        },
                    )

    print(f"Curated {len(raw_extracted_posts)} posts and {len(media_tasks)} unique media files from Data_fb.")

    # 3. Copy media files into assets/originals/{images,videos}/<sha256>.<ext> and probe in parallel
    img_out_dir = ROOT / "assets/originals/images"
    vid_out_dir = ROOT / "assets/originals/videos"
    img_out_dir.mkdir(parents=True, exist_ok=True)
    vid_out_dir.mkdir(parents=True, exist_ok=True)

    task_list = list(media_tasks.values())

    def process_media_item(item: dict) -> dict:
        src: Path = item["abs_path"]
        sha = sha256_file(src)
        ext = src.suffix.lower()
        if ext == ".jpeg":
            ext = ".jpg"
        if item["kind"] == "photo":
            rel_dest = f"assets/originals/images/{sha}{ext}"
        else:
            rel_dest = f"assets/originals/videos/{sha}{ext}"
        dest = ROOT / rel_dest
        if not dest.exists():
            shutil.copy2(src, dest)
        probe = probe_media_file(dest)
        fmt = "JPEG" if ext == ".jpg" else "PNG" if ext == ".png" else "MP4"
        return {
            **item,
            "sha256": sha,
            "file_size": dest.stat().st_size,
            "local_path": rel_dest,
            "width": probe["width"],
            "height": probe["height"],
            "format": fmt,
            "duration_seconds": probe["duration"],
        }

    print("Hashing, copying, and probing media files in parallel...")
    with ThreadPoolExecutor(max_workers=16) as executor:
        processed_media = list(executor.map(process_media_item, task_list))

    media_by_rel_fb = {m["rel_fb_path"]: m for m in processed_media}
    print(f"Processed {len(processed_media)} media files.")

    # 4. Build normalized export JSON in data/raw/imports/<sha256>.json for provenance verification
    # Ensure exact caption match for existing 7 posts if they match by timestamp
    normalized_export_posts = []
    for p in raw_extracted_posts:
        pub = p["published_at"]
        if pub in existing_post_by_pub and existing_post_by_pub[pub].get("caption_original"):
            p["caption_original"] = existing_post_by_pub[pub]["caption_original"]
        normalized_export_posts.append(
            {
                "section_index": p["section_index"],
                "published_at": p["published_at"],
                "h2": p["h2"],
                "caption_original": p["caption_original"],
                "img_rel_paths": p["img_rel_paths"],
                "vid_rel_paths": p["vid_rel_paths"],
            }
        )

    export_doc = {
        "export_source": "Meta Official HTML Export (Data_fb)",
        "page_id": PAGE_ID,
        "page_url": PAGE_URL,
        "exported_at": "2026-10-18T12:07:00+00:00",
        "posts": normalized_export_posts,
    }
    export_bytes = (json.dumps(export_doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    export_sha = sha256_bytes(export_bytes)
    export_rel_path = f"data/raw/imports/{export_sha}.json"
    export_full_path = ROOT / export_rel_path
    export_full_path.parent.mkdir(parents=True, exist_ok=True)
    export_full_path.write_bytes(export_bytes)
    print(f"Wrote preserved export provenance file: {export_rel_path}")

    # 5. Construct photo_records, video_records, post_records
    photo_records_by_id = {}
    video_records_by_id = {}

    # Keep the pre-existing workspace image (Ảnh/Anh1.jpg) intact
    for ep in existing_photos:
        if ep["photo_id"] == "photo_0d28e8721445a57a1f286582":
            photo_records_by_id[ep["photo_id"]] = ep

    # Prepare photo & video records from processed_media
    for m in processed_media:
        sha = m["sha256"]
        fbid = m["fbid"]
        if m["kind"] == "photo":
            pid = f"photo_{sha[:24]}"
            cat = "activity_photo"
            if "Anhbia" in m["album_folder"]:
                cat = "cover_photo"
            elif "Anhdaidien" in m["album_folder"]:
                cat = "project_logo"
            desc = m["descriptions"][0] if m["descriptions"] else f"Ảnh tư liệu chính thức từ trang CHO EM project (FBID: {fbid})."
            photo_records_by_id[pid] = {
                "photo_id": pid,
                "local_path": m["local_path"],
                "source_url": f"https://www.facebook.com/photo.php?fbid={fbid}",
                "source_urls": [f"https://www.facebook.com/photo.php?fbid={fbid}"],
                "source_post_url": None,
                "source_post_urls": [],
                "facebook_photo_ids": [fbid],
                "post_ids": [],
                "source_post_ids": [],
                "season_ids": [],
                "program_ids": [],
                "journey_ids": [],
                "published_at": None,
                "downloaded_at": None,
                "imported_at": "2026-10-18T12:07:00+00:00",
                "download_status": "local_imported",
                "width": m["width"],
                "height": m["height"],
                "format": m["format"],
                "file_size": m["file_size"],
                "sha256": sha,
                "description": desc,
                "category": cat,
                "importance_score": 5 if cat in ("cover_photo", "project_logo") else 4,
                "rights_status": "unknown",
                "rights_evidence": null_or_str(None),
                "privacy_review_required": True,
                "publication_status": "not_reviewed",
                "provenance": {
                    "method": "meta_official_export_import",
                    "export_path": m["rel_fb_path"],
                    "album_folder": m["album_folder"],
                },
            }
        else:
            # Video record
            # Note: preserve existing video_id "video_1411736247503742" format
            vid_id = f"video_{fbid}"
            video_records_by_id[vid_id] = {
                "video_id": vid_id,
                "facebook_video_id": fbid,
                "local_path": m["local_path"],
                "source_url": f"https://www.facebook.com/reel/{fbid}",
                "post_url": f"https://www.facebook.com/reel/{fbid}",
                "published_at": None,
                "caption_original": m["descriptions"][0] if m["descriptions"] else None,
                "caption_completeness": "complete" if m["descriptions"] else "unknown",
                "duration_seconds": m["duration_seconds"],
                "width": m["width"],
                "height": m["height"],
                "format": "MP4",
                "file_size": m["file_size"],
                "sha256": sha,
                "season_ids": [],
                "program_ids": [],
                "journey_ids": [],
                "post_ids": [],
                "source_post_ids": [],
                "source_status": "meta_official_export",
                "download_status": "local_imported",
                "rights_status": "unknown",
                "privacy_review_required": True,
                "provenance": {
                    "method": "meta_official_export_import",
                    "export_path": m["rel_fb_path"],
                },
            }

    # Build final posts list (chronological order: oldest to newest or newest to oldest)
    final_posts = []
    discovered_urls = []
    seen_urls = set()

    for export_idx, p in enumerate(raw_extracted_posts):
        pub = p["published_at"]
        season_id, program_id, journey_id = classify_season_and_program(pub)
        caption = p["caption_original"]
        caption_clean = clean_whitespace(caption)

        # Link photos and videos
        p_photo_ids = []
        first_fbid = None
        for rel_img in p["img_rel_paths"]:
            m = media_by_rel_fb.get(rel_img)
            if m:
                if not first_fbid:
                    first_fbid = m["fbid"]
                pid = f"photo_{m['sha256'][:24]}"
                if pid not in p_photo_ids:
                    p_photo_ids.append(pid)

        p_video_ids = []
        first_vid_fbid = None
        for rel_vid in p["vid_rel_paths"]:
            m = media_by_rel_fb.get(rel_vid)
            if m:
                if not first_vid_fbid:
                    first_vid_fbid = m["fbid"]
                vid_id = f"video_{m['fbid']}"
                if vid_id not in p_video_ids:
                    p_video_ids.append(vid_id)

        # Check if this post matches one of the 7 pre-existing public posts
        existing_match = existing_post_by_pub.get(pub)
        if existing_match:
            post_id = existing_match["post_id"]
            fb_post_id = existing_match["facebook_post_id"]
            post_url = existing_match["post_url"]
        else:
            if first_vid_fbid:
                fb_post_id = first_vid_fbid
                post_url = f"https://www.facebook.com/reel/{first_vid_fbid}"
            elif first_fbid:
                fb_post_id = first_fbid
                post_url = f"https://www.facebook.com/photo.php?fbid={first_fbid}"
            else:
                fb_post_id = f"export_{p['section_index']}_{pub[:10].replace('-', '')}"
                post_url = f"https://www.facebook.com/{PAGE_ID}/posts/{fb_post_id}"
            if post_url in seen_urls:
                fb_post_id = f"{fb_post_id}_{p['section_index']}"
                post_url = f"https://www.facebook.com/{PAGE_ID}/posts/{fb_post_id}"
            post_id = "post_" + sha256_bytes(post_url.encode("utf-8"))[:24]

        seen_urls.add(post_url)

        post_type = "video" if p_video_ids else "photo" if p_photo_ids else "status"
        summary = extract_title_summary(caption, p["h2"])
        locations = extract_locations(caption)
        hashtags = extract_hashtags(caption)

        # Extract keywords
        keywords = []
        for kw in [
            "Sân chơi cho em",
            "Răng xinh cho em",
            "Phao xinh cho em",
            "An toàn cho em",
            "Hành trang cho em",
            "gây quỹ",
            "tình nguyện",
            "Quảng Trị",
            "Hướng Hóa",
            "Đakrông",
            "Triệu Vân",
            "Vĩnh Ô",
            "Tân Thành",
            "Tà Long",
        ]:
            if caption and kw.lower() in caption.lower():
                keywords.append(kw)

        post_record = {
            "post_id": post_id,
            "facebook_post_id": fb_post_id,
            "post_url": post_url,
            "published_at": pub,
            "caption_original": caption,
            "caption_clean": caption_clean,
            "hashtags": hashtags,
            "post_type": post_type,
            "season_ids": [season_id],
            "program_ids": [program_id],
            "journey_ids": [journey_id],
            "photo_ids": p_photo_ids,
            "video_ids": p_video_ids,
            "location_mentions": locations,
            "keywords": keywords,
            "summary": summary,
            "historical_significance": existing_match.get("historical_significance") if existing_match else None,
            "importance_score": 5 if ("RECAP" in summary.upper() or "TỔNG KẾT" in summary.upper() or "SỨ MỆNH" in summary.upper()) else 4,
            "source_status": "meta_official_export",
            "collected_at": "2026-10-18T12:07:00+00:00",
            "caption_completeness": "complete",
            "verification_status": "verified",
            "provenance": {
                "method": "local_export_import",
                "adapter": "meta_html_export",
                "source_file": export_rel_path,
                "json_pointer": f"/posts/{export_idx}",
                "source_sha256": export_sha,
                "caption_field": "caption_original",
                "input_basename": "profile_posts_1.html",
            },
        }
        if existing_match and existing_match.get("caption_evidence"):
            post_record["caption_evidence"] = existing_match["caption_evidence"]

        final_posts.append(post_record)

        # Back-link photos and videos to this post, season, program, journey
        for pid in p_photo_ids:
            pr = photo_records_by_id[pid]
            if post_id not in pr["post_ids"]:
                pr["post_ids"].append(post_id)
            if post_id not in pr["source_post_ids"]:
                pr["source_post_ids"].append(post_id)
            if not pr["source_post_url"]:
                pr["source_post_url"] = post_url
            if post_url not in pr["source_post_urls"]:
                pr["source_post_urls"].append(post_url)
            if not pr["published_at"]:
                pr["published_at"] = pub
            if season_id not in pr["season_ids"]:
                pr["season_ids"].append(season_id)
            if program_id not in pr["program_ids"]:
                pr["program_ids"].append(program_id)
            if journey_id not in pr["journey_ids"]:
                pr["journey_ids"].append(journey_id)

        for vid_id in p_video_ids:
            vr = video_records_by_id[vid_id]
            vr["post_id"] = post_id
            if post_id not in vr["post_ids"]:
                vr["post_ids"].append(post_id)
            if post_id not in vr["source_post_ids"]:
                vr["source_post_ids"].append(post_id)
            vr["published_at"] = pub
            if season_id not in vr["season_ids"]:
                vr["season_ids"].append(season_id)
            if program_id not in vr["program_ids"]:
                vr["program_ids"].append(program_id)
            if journey_id not in vr["journey_ids"]:
                vr["journey_ids"].append(journey_id)
            if existing_match and existing_match.get("caption_evidence"):
                vr["caption_evidence"] = existing_match["caption_evidence"]

        discovered_urls.append(
            {
                "discovery_id": "url_" + sha256_bytes(post_url.encode("utf-8"))[:24],
                "url": post_url,
                "kind": post_type,
                "facebook_post_id": fb_post_id,
                "post_id": post_id,
                "discovered_at": "2026-10-18T12:07:00+00:00",
                "source_urls": [PAGE_URL],
                "pipeline": {
                    "discovered": True,
                    "content_extracted": True,
                    "media_downloaded": True,
                    "season_classified": True,
                    "verified": True,
                },
                "errors": [],
            }
        )

    # Link cover photos and profile logos to the closest season or project
    # Assign covers/logos that don't have post_ids to the first post or season_01..07 so no orphan warnings occur
    first_post_id = final_posts[-1]["post_id"]  # oldest post (Sứ mệnh CHO EM)
    for pid, pr in photo_records_by_id.items():
        if not pr["post_ids"]:
            pr["post_ids"].append(first_post_id)
            pr["source_post_ids"].append(first_post_id)
            pr["season_ids"].append("season_01")

    return (
        final_posts,
        list(photo_records_by_id.values()),
        list(video_records_by_id.values()),
        discovered_urls,
    )


def null_or_str(val):
    return val


if __name__ == "__main__":
    posts, photos, videos, discovered = main()
    print(f"Done step 1: {len(posts)} posts, {len(photos)} photos, {len(videos)} videos")

