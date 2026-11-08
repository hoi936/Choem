#!/usr/bin/env python3
"""Archive explicit, public Facebook CDN image URLs evidenced by local snapshots.

No discovery, URL rewriting, credentials, retries, or publication authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import archive


MAX_BYTES = 50 * 1024 * 1024
MIN_INTERVAL = 3.0


class StopAccess(Exception):
    """The server indicates an access boundary; stop the entire manifest."""


def validate_url(url):
    if not isinstance(url, str) or not url or any(c.isspace() or ord(c) < 32 for c in url):
        raise ValueError("source_url must be a literal HTTPS URL without whitespace")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if (parsed.scheme != "https" or not (host == "fbcdn.net" or host.endswith(".fbcdn.net"))
            or parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment):
        raise ValueError("Only explicit public HTTPS fbcdn.net image URLs are permitted")
    return url


class RestrictedRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        try:
            validate_url(newurl)
        except ValueError as exc:
            raise StopAccess("Redirect leaves the permitted HTTPS Facebook CDN") from exc
        # Redirect targets are not present in the evidence manifest. Do not follow.
        raise StopAccess("CDN redirected the explicit URL; review a fresh public source snapshot")


def manifest_records(root, manifest):
    document = archive.read_json(manifest)
    if not isinstance(document, list):
        raise ValueError("Manifest must be a JSON array")
    validated = []
    for index, item in enumerate(document):
        if not isinstance(item, dict):
            raise ValueError(f"Manifest item {index} must be an object")
        validate_url(item.get("source_url"))
        if item.get("rights_status", "unknown") != "unknown":
            raise ValueError("Public CDN retrieval does not establish reuse rights; use rights_status unknown")
        snapshot_name = item.get("provenance_snapshot")
        if not isinstance(snapshot_name, str) or not snapshot_name:
            raise ValueError(f"Manifest item {index} requires provenance_snapshot")
        snapshot = (root / snapshot_name).resolve()
        try:
            relative = snapshot.relative_to(root)
        except ValueError as exc:
            raise ValueError("provenance_snapshot must be inside the archive root") from exc
        if not snapshot.is_file():
            raise ValueError(f"Source snapshot does not exist: {snapshot_name}")
        if item.get("description") is not None and not isinstance(item["description"], str):
            raise ValueError("description must be a string or null")
        if item.get("source_post_url"):
            archive.canonical_url(item["source_post_url"])
        validated.append({**item, "provenance_snapshot": relative.as_posix(),
                          "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest()})
    return validated


def locate_post(root, item):
    posts = archive.read_json(root / "data/raw/posts.json", [])
    if item.get("post_id"):
        if not any(post.get("post_id") == item["post_id"] for post in posts):
            raise ValueError("Manifest post_id does not exist")
        return item["post_id"]
    if item.get("source_post_url"):
        canonical = archive.canonical_url(item["source_post_url"])
        for post in posts:
            if post.get("post_url") and archive.canonical_url(post["post_url"]) == canonical:
                return post["post_id"]
    return None


def fetch_image(opener, url, target):
    request = Request(url, headers={"User-Agent": "CHO-EM-Archive/1.0 (public image archival)",
                                    "Accept": "image/*"}, method="GET")
    try:
        with opener.open(request, timeout=30) as response:
            final_url = response.geturl()
            if final_url != url:
                raise StopAccess("Response URL changed; explicit URL only")
            content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                sample = response.read(8192).lower()
                if any(marker in sample for marker in (b"captcha", b"checkpoint", b"login", b"log in")):
                    raise StopAccess("Login or CAPTCHA response; collection stopped")
                raise ValueError(f"Expected image response, received {content_type}")
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_BYTES:
                raise ValueError("Image exceeds the 50 MiB response limit")
            total = 0
            with target.open("wb") as stream:
                while True:
                    chunk = response.read(min(65536, MAX_BYTES + 1 - total))
                    if not chunk:
                        break
                    if total == 0 and chunk.lstrip().startswith((b"<", b"{", b"[")):
                        sample = chunk[:8192].lower()
                        if any(marker in sample for marker in (b"captcha", b"checkpoint", b"login", b"log in")):
                            raise StopAccess("Login or CAPTCHA body returned as an image; collection stopped")
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError("Image exceeds the 50 MiB response limit")
                    stream.write(chunk)
            return {"http_status": response.status, "content_type": content_type, "bytes": total}
    except HTTPError as exc:
        if exc.code in (401, 403, 407, 429):
            raise StopAccess(f"HTTP {exc.code}; access boundary reached") from exc
        # A textual denial can also arrive with another error status.
        sample = exc.read(8192).lower()
        if any(marker in sample for marker in (b"captcha", b"checkpoint", b"login", b"log in")):
            raise StopAccess(f"HTTP {exc.code} login/CAPTCHA response") from exc
        raise


def annotate_download(root, item, imported, timestamp, manifest_name):
    photos = archive.read_json(root / "data/raw/photos.json", [])
    record = next(photo for photo in photos if photo["photo_id"] == imported["photo_id"])
    retrieval = {"method": "public_https_download", "source_url": item["source_url"],
                 "source_post_url": item.get("source_post_url"), "retrieved_at": timestamp,
                 "provenance_snapshot": item["provenance_snapshot"],
                 "snapshot_sha256": item["snapshot_sha256"], "manifest_file": manifest_name}
    # One evidence edge per source/snapshot; reruns do not inflate provenance.
    existing = record.setdefault("retrievals", [])
    if not any(edge.get("source_url") == item["source_url"] and
               edge.get("snapshot_sha256") == item["snapshot_sha256"] for edge in existing):
        existing.append(retrieval)
    record["download_status"] = "downloaded"
    record["downloaded_at"] = record.get("downloaded_at") or timestamp
    # Temporary transport files disappear after import; permanent provenance is
    # the source URL plus the preserved snapshot, never the temporary pathname.
    record["local_sources"] = [path for path in record.get("local_sources", [])
                               if not path.startswith("data/raw/imports/.public-media-")]
    # Retain all source links even when two URLs contain identical original bytes.
    record.setdefault("source_urls", [])
    if item["source_url"] not in record["source_urls"]:
        record["source_urls"].append(item["source_url"])
    if item.get("source_post_url"):
        if not record.get("source_post_url"):
            record["source_post_url"] = item["source_post_url"]
        record.setdefault("source_post_urls", [])
        if item["source_post_url"] not in record["source_post_urls"]:
            record["source_post_urls"].append(item["source_post_url"])
    if record.get("description") is None and item.get("description"):
        record["description"] = item["description"]
    if not imported["deduplicated"]:
        record["provenance"] = retrieval
    # Existing reviewed decisions are never downgraded. Newly imported public
    # images already have unknown rights and privacy_review_required=True.
    archive.atomic_json(root / "data/raw/photos.json", photos)
    media_index = archive.read_json(root / "data/processed/media_index.json", [])
    replacement = {"media_id": record["photo_id"], "media_type": "photo", **record}
    media_index = [replacement if media.get("media_id") == record["photo_id"] else media
                   for media in media_index]
    archive.atomic_json(root / "data/processed/media_index.json", media_index)
    archive.atomic_json(root / "data/unclassified/media.json",
                        [media for media in media_index if not media.get("season_ids")])
    return record


def download_manifest(root, manifest, dry_run=False):
    records = manifest_records(root, manifest)
    # Validate referenced posts before making any requests.
    post_ids = [locate_post(root, item) for item in records]
    if dry_run:
        return {"dry_run": True, "validated_images": len(records), "network_requests": 0,
                "interval_seconds": MIN_INTERVAL, "max_response_bytes": MAX_BYTES}
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Pillow must be installed before any download") from exc
    attempts_path = root / "research/download_attempts.json"
    attempts = archive.read_json(attempts_path, [])
    if not isinstance(attempts, list):
        raise ValueError("research/download_attempts.json must contain an array")
    opener = build_opener(RestrictedRedirects())
    previous_request = None
    result = {"manifest_entries": len(records), "downloaded": 0, "skipped_existing": 0,
              "failed": 0, "stopped": False}
    try:
        manifest_name = manifest.resolve().relative_to(root).as_posix()
    except ValueError:
        manifest_name = manifest.name
    for item, post_id in zip(records, post_ids):
        photos = archive.read_json(root / "data/raw/photos.json", [])
        known = next((photo for photo in photos if item["source_url"] in photo.get("source_urls", [])
                      and photo.get("download_status") == "downloaded"), None)
        if known and known.get("local_path"):
            original = root / known["local_path"]
            if original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest() == known.get("sha256"):
                # Reconcile links/checkpoint after a prior interrupted import.
                with archive.archive_lock(root):
                    imported = archive.import_media(root, original, item["source_url"], post_id=post_id)
                    annotate_download(root, item, imported, archive.now(), manifest_name)
                result["skipped_existing"] += 1
                continue
        if previous_request is not None:
            remaining = MIN_INTERVAL - (time.monotonic() - previous_request)
            if remaining > 0:
                time.sleep(remaining)
        attempt = {"source_url": item["source_url"], "source_post_url": item.get("source_post_url"),
                   "provenance_snapshot": item["provenance_snapshot"], "started_at": archive.now(),
                   "status": "started", "manifest_file": manifest_name}
        attempts.append(attempt)
        archive.atomic_json(attempts_path, attempts)
        previous_request = time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix=".public-media-", dir=root / "data/raw/imports") as temporary:
                downloaded = Path(temporary) / "original"
                attempt.update(fetch_image(opener, item["source_url"], downloaded))
                with archive.archive_lock(root):
                    imported = archive.import_media(root, downloaded, item["source_url"], post_id=post_id)
                    record = annotate_download(root, item, imported, archive.now(), manifest_name)
                attempt.update({"status": "downloaded", "photo_id": imported["photo_id"],
                                "local_path": record["local_path"], "sha256": record["sha256"]})
            result["downloaded"] += 1
        except (StopAccess, HTTPError, URLError, OSError, ValueError, RuntimeError) as exc:
            attempt.update({"status": "access_stopped" if isinstance(exc, StopAccess) else "error",
                            "error": f"{type(exc).__name__}: {exc}"})
            archive.log(root, "download-public-media " + json.dumps(attempt, ensure_ascii=False), error=True)
            result["failed"] += 1
            if isinstance(exc, StopAccess):
                result["stopped"] = True
        attempt["finished_at"] = archive.now()
        archive.atomic_json(attempts_path, attempts)
        if result["stopped"]:
            break
    archive.checkpoint(root, "download-public-media", result)
    archive.log(root, "download-public-media " + json.dumps(result, ensure_ascii=False))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Validate local provenance and URLs; no requests")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if not args.dry_run:
            with archive.archive_lock(root):
                archive.initialize(root)
        result = download_manifest(root, args.manifest, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("stopped") or result.get("failed") else 0
    except (ValueError, OSError, RuntimeError) as exc:
        archive.log(root, f"download-public-media: {type(exc).__name__}: {exc}", error=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
