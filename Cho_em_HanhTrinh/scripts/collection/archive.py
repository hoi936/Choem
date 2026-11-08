#!/usr/bin/env python3
"""Conservative, resumable CHO EM archive import. No network requests."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


PAGE_URL = "https://www.facebook.com/profile.php?id=100094610840245"
ARRAY_FILES = [
    "data/raw/posts.json", "data/raw/photos.json", "data/raw/videos.json",
    "data/raw/albums.json", "data/raw/discovered_urls.json",
    *[f"data/processed/{name}.json" for name in (
        "seasons", "programs", "journeys", "timeline", "milestones", "stories",
        "featured_content", "media_index")],
    "data/unclassified/posts.json", "data/unclassified/media.json",
    "research/evidence_map.json",
]
DIRECTORIES = [
    "data/raw/imports", "data/raw/posts", "data/seasons", "assets/originals/images",
    "assets/originals/videos", "assets/seasons", "assets/project/logos",
    "assets/project/covers", "assets/project/featured", "assets/thumbnails",
    "content", "research", "scripts/collection", "scripts/processing",
    "scripts/validation", "logs", "reports",
]
FLAGS = ("discovered", "content_extracted", "media_downloaded", "season_classified", "verified")
RIGHTS = ("unknown", "permission_confirmed", "owned", "licensed", "restricted")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".archive-", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def archive_lock(root):
    """Single writer on POSIX and Windows; OS releases locks after interruption."""
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".archive.lock").open("a+b") as stream:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            if stream.read(1) == b"":
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def log(root, message, error=False):
    path = root / "logs" / ("errors.log" if error else "collection.log")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"{now()} {message}\n")


def initialize(root):
    for name in DIRECTORIES:
        (root / name).mkdir(parents=True, exist_ok=True)
    for name in ARRAY_FILES:
        if not (root / name).exists():
            atomic_json(root / name, [])
    if not (root / "data/raw/page_info.json").exists():
        atomic_json(root / "data/raw/page_info.json", {
            "page_id": "100094610840245", "page_url": PAGE_URL,
            "project_name": "CHO EM", "verification_status": "unknown",
            "source_status": "user_provided_seed", "collected_at": None,
            "research_notes": "Tên và URL do người dùng cung cấp; chưa xác minh nội dung trang.",
        })
    if not (root / "data/processed/project_info.json").exists():
        atomic_json(root / "data/processed/project_info.json", {
            "project_id": "cho_em", "name": "CHO EM", "name_meaning": None,
            "founded_at": None, "origin_story": None, "mission": None,
            "vision": None, "objectives": [], "core_values": [],
            "partners": [], "source_urls": [], "verification_status": "unknown",
        })
    for name in ("collection.log", "errors.log"):
        (root / "logs" / name).touch(exist_ok=True)
    if not (root / "research/collection_progress.json").exists():
        checkpoint(root, "initialized")
    return status(root)


def status(root):
    counts = {}
    for name in ARRAY_FILES:
        value = read_json(root / name, [])
        counts[name] = len(value) if isinstance(value, list) else None
    discoveries = read_json(root / "data/raw/discovered_urls.json", [])
    return {
        "counts": counts,
        "pipeline_counts": {flag: sum(bool(d.get("pipeline", {}).get(flag)) for d in discoveries)
                            for flag in FLAGS},
        "seasons_verified": sum(s.get("verification_status") == "verified"
                                for s in read_json(root / "data/processed/seasons.json", [])),
        "historical_coverage": "unknown",
        "empty_arrays_are_collected_data": False,
    }


def checkpoint(root, operation, details=None):
    prior = read_json(root / "research/collection_progress.json", {})
    prior.update({"updated_at": now(), "last_operation": operation,
                  "last_operation_details": details, **status(root)})
    # Existing access limitations and research notes survive the refresh.
    atomic_json(root / "research/collection_progress.json", prior)


def canonical_url(value):
    """Remove tracking, retaining identifiers; reject non-Facebook URLs."""
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("https", "http") or host not in (
        "facebook.com", "www.facebook.com", "m.facebook.com", "mbasic.facebook.com",
        "web.facebook.com", "fb.watch", "www.fb.watch",
    ) or parsed.username or parsed.password:
        raise ValueError("Expected a public Facebook or fb.watch URL")
    path = parsed.path.rstrip("/") or "/"
    query = parse_qs(parsed.query)
    keep = {key: values[-1] for key, values in query.items()
            if key in ("id", "story_fbid", "fbid", "set", "v")}
    if path in ("/story.php", "/permalink.php") and "id" in keep and "story_fbid" in keep:
        path = f"/{keep['id']}/posts/{keep['story_fbid']}"
        keep = {}
    host = "fb.watch" if host.endswith("fb.watch") else "www.facebook.com"
    return urlunparse(("https", host, path, "", urlencode(sorted(keep.items())), ""))


def url_info(url):
    parsed = urlparse(url)
    match = re.search(r"/posts/([^/]+)", parsed.path)
    if match:
        return "post", match.group(1)
    query = parse_qs(parsed.query)
    if "story_fbid" in query:
        return "post", query["story_fbid"][0]
    if "fbid" in query and parsed.path in ("/photo.php", "/photo"):
        return "photo", None
    if "/videos/" in parsed.path or "v" in query or parsed.hostname == "fb.watch":
        return "video", None
    if "set" in query or "/albums/" in parsed.path:
        return "album", None
    return "page_or_unknown", None


def discover(root, urls, source_url=None):
    records = read_json(root / "data/raw/discovered_urls.json", [])
    existing = {item["url"]: item for item in records}
    added = 0
    for value in urls:
        url = canonical_url(value)
        if url in existing:
            if source_url and source_url not in existing[url]["source_urls"]:
                existing[url]["source_urls"].append(source_url)
            continue
        kind, facebook_id = url_info(url)
        record = {
            "discovery_id": "url_" + digest_bytes(url.encode())[:24],
            "url": url, "kind": kind, "facebook_post_id": facebook_id,
            "post_id": None, "discovered_at": now(),
            "source_urls": [source_url] if source_url else [],
            "pipeline": {flag: flag == "discovered" for flag in FLAGS}, "errors": [],
        }
        records.append(record)
        existing[url] = record
        added += 1
    atomic_json(root / "data/raw/discovered_urls.json", records)
    checkpoint(root, "discover", {"added": added})
    log(root, f"discover added={added} total={len(records)}")
    return {"added": added, "total": len(records)}


def export_entries(document, requested_format):
    adapter = requested_format
    if isinstance(document, dict):
        if "your_posts_v2" in document:
            entries, adapter = document["your_posts_v2"], "facebook"
        elif "posts_v2" in document:
            entries, adapter = document["posts_v2"], "facebook"
        elif "posts" in document:
            entries = document["posts"]
        else:
            raise ValueError("Unknown export object; expected posts/your_posts_v2/posts_v2 array")
    elif isinstance(document, list):
        entries = document
    else:
        raise ValueError("Export must be an object with posts or an array")
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        raise ValueError("Every exported post must be an object")
    if requested_format != "auto" and adapter not in ("auto", requested_format):
        raise ValueError("Requested export format contradicts the detected wrapper")
    return entries, adapter


def extract_caption(entry, adapter, declared=None):
    if "caption_original" in entry:
        caption = entry["caption_original"]
        field = "caption_original"
        completeness = entry.get("caption_completeness", "unknown")
    elif adapter in ("facebook", "auto") and isinstance(entry.get("data"), list):
        parts = [item["post"] for item in entry["data"]
                 if isinstance(item, dict) and isinstance(item.get("post"), str)]
        if len(parts) > 1:
            raise ValueError("Multiple data[].post fields require review; supply a normalized caption_original")
        caption = parts[0] if parts else None
        field = "data[*].post" if parts else None
        completeness = "complete" if parts and adapter == "facebook" else "unknown"
    elif isinstance(entry.get("post"), str):
        caption, field, completeness = entry["post"], "post", "unknown"
    elif isinstance(entry.get("message"), str):
        caption, field, completeness = entry["message"], "message", "unknown"
    else:
        caption, field, completeness = None, None, "unknown"
    if caption is not None and not isinstance(caption, str):
        raise ValueError("caption_original must be a string or null")
    if declared:
        completeness = declared
    if completeness not in ("complete", "partial", "unknown"):
        raise ValueError("caption_completeness must be complete, partial or unknown")
    if caption is None:
        completeness = "unknown"
    return caption, field, completeness


def published_time(entry):
    value = entry.get("published_at", entry.get("timestamp"))
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    if isinstance(value, str):
        # Keep year/month precision rather than inventing a calendar date.
        if re.fullmatch(r"\d{4}(-\d{2})?", value):
            datetime.strptime(value, "%Y-%m" if "-" in value else "%Y")
            return value
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid published_at: {value}") from exc
        return value
    raise ValueError("published_at must be ISO 8601 or a Unix timestamp")


def list_field(entry, key):
    value = entry.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array")
    return value


def preserve_merge(existing, incoming):
    """Augment references without silently replacing conflicting original evidence."""
    if not existing:
        return incoming
    result = dict(existing)
    for key, value in incoming.items():
        if key == "provenance":
            continue
        if isinstance(value, list):
            result[key] = list(existing.get(key) or [])
            for item in value:
                if item not in result[key]:
                    result[key].append(item)
        elif result.get(key) is None:
            result[key] = value
    return result


def ensure_references(root, entry):
    for field, collection, identifier in (
        ("season_ids", "seasons", "season_id"),
        ("program_ids", "programs", "program_id"),
        ("journey_ids", "journeys", "journey_id"),
    ):
        requested = list_field(entry, field)
        known = {item[identifier] for item in read_json(root / f"data/processed/{collection}.json", [])}
        if set(requested) - known:
            raise ValueError(f"Unknown {field}: {sorted(set(requested) - known)}; research evidence first")
    for field, collection, identifier in (
        ("photo_ids", "photos", "photo_id"), ("video_ids", "videos", "video_id"),
    ):
        requested = list_field(entry, field)
        known = {item[identifier] for item in read_json(root / f"data/raw/{collection}.json", [])}
        if set(requested) - known:
            raise ValueError(f"Unknown {field}: import media first or omit these references")


def import_export(root, source, requested_format="auto", completeness=None):
    source_bytes = source.read_bytes()
    source_hash = digest_bytes(source_bytes)
    document = json.loads(source_bytes.decode("utf-8-sig"))
    entries, adapter = export_entries(document, requested_format)
    pointer_prefix = ""
    if isinstance(document, dict):
        wrapper = next(key for key in ("your_posts_v2", "posts_v2", "posts") if key in document)
        pointer_prefix = "/" + wrapper
    source_relative = f"data/raw/imports/{source_hash}.json"
    archived_source = root / source_relative
    if not archived_source.exists():
        archived_source.parent.mkdir(parents=True, exist_ok=True)
        # Preserve exact export bytes, including original Unicode and line endings.
        with tempfile.NamedTemporaryFile(dir=archived_source.parent, delete=False) as stream:
            stream.write(source_bytes)
            temporary = stream.name
        os.replace(temporary, archived_source)
    posts = read_json(root / "data/raw/posts.json", [])
    by_id = {post["post_id"]: post for post in posts}
    by_url = {post["post_url"]: post for post in posts if post.get("post_url")}
    inserted, conflicts = 0, []
    prepared = []
    for index, entry in enumerate(entries):
        ensure_references(root, entry)
        caption, caption_field, caption_completeness = extract_caption(entry, adapter, completeness)
        url = entry.get("post_url", entry.get("url"))
        if url:
            url = canonical_url(url)
        fb_id = entry.get("facebook_post_id")
        if not fb_id and url:
            fb_id = url_info(url)[1]
        if fb_id is not None:
            fb_id = str(fb_id)
        published_at = published_time(entry)
        # Fallback identity excludes export path/order: repeat exports remain stable.
        identity = fb_id or url or json.dumps(
            {"published_at": published_at, "caption_original": caption,
             "attachments": entry.get("attachments"),
             "export_id": entry.get("post_id", entry.get("id"))},
            ensure_ascii=False, sort_keys=True)
        if not fb_id and not url and caption is None and not entry.get("post_id", entry.get("id")):
            raise ValueError(f"Post {index} has no caption, URL or ID; cannot create a reliable identity")
        post_id = "post_" + digest_bytes(identity.encode())[:24]
        prior = by_id.get(post_id) or by_url.get(url)
        if prior:
            post_id = prior["post_id"]
        clean = re.sub(r"\s+", " ", caption).strip() if caption is not None else None
        post = {
            "post_id": post_id, "facebook_post_id": fb_id, "post_url": url,
            "published_at": published_at, "caption_original": caption, "caption_clean": clean,
            "hashtags": re.findall(r"#[\w]+", caption or "", re.UNICODE),
            "post_type": entry.get("post_type", "unknown"),
            **{key: list_field(entry, key) for key in (
                "season_ids", "program_ids", "journey_ids", "photo_ids", "video_ids",
                "location_mentions", "keywords")},
            "summary": None, "historical_significance": None, "importance_score": None,
            "source_status": "imported_export", "collected_at": now(),
            "caption_completeness": caption_completeness, "verification_status": "unknown",
            "provenance": {"method": "local_export_import", "adapter": adapter,
                           "source_file": source_relative, "json_pointer": f"{pointer_prefix}/{index}",
                           "source_sha256": source_hash, "caption_field": caption_field,
                           "input_basename": source.name},
        }
        if prior and prior.get("caption_original") is not None and caption is not None and prior["caption_original"] != caption:
            conflicts.append({"post_id": post_id, "reason": "caption_changed_original_preserved",
                              "incoming_source": source_relative, "entry_index": index})
            for field in ("caption_original", "caption_clean", "hashtags", "caption_completeness"):
                post[field] = prior.get(field)
        merged = preserve_merge(prior, post)
        if prior and prior.get("caption_original") is None and caption is not None:
            merged["caption_completeness"] = caption_completeness
        if prior is None:
            inserted += 1
        by_id[post_id] = merged
        if url:
            by_url[url] = merged
        prepared.append(merged)
    # Validation finishes before changing any index. Original input is safely archived.
    posts = list(by_id.values())
    atomic_json(root / "data/raw/posts.json", posts)
    for post in prepared:
        atomic_json(root / "data/raw/posts" / (post["post_id"] + ".json"), post)
    urls = [post["post_url"] for post in prepared if post.get("post_url")]
    if urls:
        discover(root, urls, source_relative)
        discoveries = read_json(root / "data/raw/discovered_urls.json", [])
        for record in discoveries:
            post = by_url.get(record["url"])
            if post:
                record["post_id"] = post["post_id"]
                record["pipeline"]["content_extracted"] |= post.get("caption_original") is not None
                record["pipeline"]["season_classified"] |= bool(post.get("season_ids"))
                record["pipeline"]["verified"] |= post.get("verification_status") == "verified"
        atomic_json(root / "data/raw/discovered_urls.json", discoveries)
    atomic_json(root / "data/unclassified/posts.json", [p for p in posts if not p.get("season_ids")])
    if conflicts:
        path = root / "research/import_conflicts.json"
        prior_conflicts = read_json(path, [])
        for conflict in conflicts:
            if conflict not in prior_conflicts:
                prior_conflicts.append(conflict)
        atomic_json(path, prior_conflicts)
    result = {"inserted": inserted, "total": len(posts), "conflicts": len(conflicts),
              "archived_source": source_relative}
    checkpoint(root, "import-export", result)
    log(root, "import-export " + json.dumps(result, ensure_ascii=False))
    return result


def import_media(root, source, source_url=None, post_id=None, rights_status="unknown", rights_evidence=None):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required to verify images; install with python -m pip install Pillow") from exc
    if rights_status not in RIGHTS:
        raise ValueError("Unknown rights_status")
    if rights_status in ("permission_confirmed", "licensed", "owned") and not rights_evidence:
        raise ValueError("rights_evidence is required for confirmed rights")
    posts = read_json(root / "data/raw/posts.json", [])
    post = next((item for item in posts if item["post_id"] == post_id), None)
    if post_id and post is None:
        raise ValueError("Unknown post_id")
    original = source.read_bytes()
    sha256 = digest_bytes(original)
    with Image.open(BytesIO(original)) as picture:
        picture.verify()
    with Image.open(BytesIO(original)) as picture:
        picture.load()
        width, height, image_format = picture.width, picture.height, picture.format
    extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "GIF": ".gif",
                 "TIFF": ".tiff", "BMP": ".bmp", "AVIF": ".avif"}.get(image_format, ".image")
    relative = f"assets/originals/images/{sha256}{extension}"
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if digest_bytes(destination.read_bytes()) != sha256:
            raise ValueError("Existing original hash mismatch; refusing to replace")
    else:
        handle, temporary = tempfile.mkstemp(prefix=".media-", dir=destination.parent)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    photo_id = "photo_" + sha256[:24]
    photos = read_json(root / "data/raw/photos.json", [])
    prior = next((item for item in photos if item.get("sha256") == sha256), None)
    local_source = None
    try:
        local_source = str(source.resolve().relative_to(root.resolve())).replace(os.sep, "/")
    except ValueError:
        pass
    record = {
        "photo_id": photo_id, "local_path": relative, "source_url": source_url,
        "source_urls": [source_url] if source_url else [],
        "source_post_url": post.get("post_url") if post else None,
        "source_post_urls": [post["post_url"]] if post and post.get("post_url") else [],
        "post_ids": [post_id] if post_id else [],
        "source_post_ids": [post_id] if post_id else [],
        **{key: list(post.get(key) or []) if post else []
           for key in ("season_ids", "program_ids", "journey_ids")},
        "published_at": post.get("published_at") if post else None,
        "downloaded_at": None, "imported_at": now(), "download_status": "local_imported",
        "width": width, "height": height, "format": image_format,
        "file_size": len(original), "sha256": sha256, "description": None,
        "category": None, "importance_score": None, "rights_status": rights_status,
        "rights_evidence": rights_evidence, "privacy_review_required": True,
        "publication_status": "not_reviewed", "local_sources": [local_source] if local_source else [],
        "provenance": {"method": "local_original_import", "input_basename": source.name},
    }
    merged = preserve_merge(prior, record)
    if prior:
        photos = [merged if item.get("photo_id") == prior["photo_id"] else item for item in photos]
        photo_id = merged["photo_id"]
    else:
        photos.append(record)
    atomic_json(root / "data/raw/photos.json", photos)
    media_index = read_json(root / "data/processed/media_index.json", [])
    media_record = {"media_id": photo_id, "media_type": "photo", **merged}
    existing_media = next((item for item in media_index if item.get("media_id") == photo_id), None)
    if existing_media:
        media_index = [media_record if item.get("media_id") == photo_id else item for item in media_index]
    else:
        media_index.append(media_record)
    atomic_json(root / "data/processed/media_index.json", media_index)
    if post:
        if photo_id not in post["photo_ids"]:
            post["photo_ids"].append(photo_id)
        atomic_json(root / "data/raw/posts.json", posts)
        atomic_json(root / "data/raw/posts" / (post_id + ".json"), post)
        atomic_json(root / "data/unclassified/posts.json", [p for p in posts if not p.get("season_ids")])
    atomic_json(root / "data/unclassified/media.json", [p for p in media_index if not p.get("season_ids")])
    result = {"photo_id": photo_id, "local_path": relative, "deduplicated": prior is not None}
    checkpoint(root, "import-media", result)
    log(root, "import-media " + json.dumps(result, ensure_ascii=False))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Initialize missing arrays/directories without overwriting data")
    commands.add_parser("status")
    discover_parser = commands.add_parser("discover")
    discover_parser.add_argument("urls", nargs="*")
    discover_parser.add_argument("--file", type=Path, help="UTF-8 text, one permitted Facebook URL per line")
    discover_parser.add_argument("--source-url")
    export_parser = commands.add_parser("import-export")
    export_parser.add_argument("file", type=Path)
    export_parser.add_argument("--format", choices=("auto", "facebook", "normalized"), default="auto")
    export_parser.add_argument("--caption-completeness", choices=("unknown", "partial", "complete"))
    media_parser = commands.add_parser("import-media")
    media_parser.add_argument("file", type=Path)
    media_parser.add_argument("--source-url")
    media_parser.add_argument("--post-id")
    media_parser.add_argument("--rights-status", choices=RIGHTS, default="unknown")
    media_parser.add_argument("--rights-evidence")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        with archive_lock(root):
            if args.command == "status":
                result = status(root)
            else:
                initialize(root)
                if args.command == "init":
                    result = status(root)
                    log(root, "init (only missing files created)")
                elif args.command == "discover":
                    urls = args.urls
                    if args.file:
                        urls.extend(line.strip() for line in args.file.read_text(encoding="utf-8").splitlines()
                                    if line.strip() and not line.lstrip().startswith("#"))
                    if not urls:
                        raise ValueError("At least one URL is required")
                    result = discover(root, urls, args.source_url)
                elif args.command == "import-export":
                    result = import_export(root, args.file, args.format, args.caption_completeness)
                else:
                    result = import_media(root, args.file, args.source_url, args.post_id,
                                          args.rights_status, args.rights_evidence)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        log(root, f"{args.command}: {type(exc).__name__}: {exc}", error=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
