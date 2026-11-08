#!/usr/bin/env python3
"""Validate the CHO EM archive offline and write honest data-quality counts.

Contract: core entity files are JSON arrays; page_info/project_info are objects.
Unknown historical facts remain null/unknown. A successful integrity check does
not mean the Facebook history has been completely collected. No source files,
credentials, image contents, or original records are changed by this command.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse


TABLES = {
    "posts": ("data/raw/posts.json", "post_id"),
    "photos": ("data/raw/photos.json", "photo_id"),
    "videos": ("data/raw/videos.json", "video_id"),
    "albums": ("data/raw/albums.json", "album_id"),
    "discovered_urls": ("data/raw/discovered_urls.json", None),
    "seasons": ("data/processed/seasons.json", "season_id"),
    "programs": ("data/processed/programs.json", "program_id"),
    "journeys": ("data/processed/journeys.json", "journey_id"),
    "timeline": ("data/processed/timeline.json", "event_id"),
    "milestones": ("data/processed/milestones.json", "milestone_id"),
    "stories": ("data/processed/stories.json", "story_id"),
    "featured_content": ("data/processed/featured_content.json", None),
    "media_index": ("data/processed/media_index.json", None),
}
REFERENCE_TABLES = {
    "season_ids": "seasons", "program_ids": "programs",
    "journey_ids": "journeys", "post_ids": "posts",
    "source_post_ids": "posts", "photo_ids": "photos", "video_ids": "videos",
    "album_ids": "albums", "milestone_ids": "milestones",
    "story_ids": "stories", "event_ids": "timeline",
}
POST_FIELDS = {
    "post_id", "facebook_post_id", "post_url", "published_at",
    "caption_original", "caption_clean", "hashtags", "post_type",
    "season_ids", "program_ids", "journey_ids", "photo_ids", "video_ids",
    "location_mentions", "keywords", "summary", "historical_significance",
    "importance_score", "source_status", "collected_at", "caption_completeness",
}
PHOTO_FIELDS = {
    "photo_id", "local_path", "source_url", "source_post_url", "season_ids",
    "program_ids", "journey_ids", "published_at", "downloaded_at", "width",
    "height", "format", "file_size", "sha256", "description", "category",
    "importance_score", "rights_status", "privacy_review_required", "download_status",
}
SEASON_FIELDS = {
    "season_id", "season_number", "official_name", "theme", "slogan",
    "start_date", "end_date", "description", "objectives", "locations",
    "program_ids", "journey_ids", "post_ids", "photo_ids", "video_ids",
    "milestone_ids", "source_urls", "verification_status", "research_notes",
}
VERIFICATION = {"verified", "inferred", "unknown"}
CAPTION_STATES = {"complete", "partial", "unknown"}
RIGHTS_STATES = {"unknown", "permission_confirmed", "owned", "licensed", "restricted"}
LOCAL_STATES = {"downloaded", "success", "local_imported", "imported", "already_exists"}
BLOCKED_DIRECTORIES = {".agents", ".aws", ".codex", ".git"}


class SnapshotJSON(HTMLParser):
    """Read already saved application/json only; never execute JavaScript."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.index = -1
        self.active = False
        self.buffer = []
        self.documents = {}

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.index += 1
            self.active = dict(attrs).get("type", "").lower() == "application/json"
            self.buffer = []

    def handle_data(self, value):
        if self.active:
            self.buffer.append(value)

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            try:
                self.documents[self.index] = json.loads("".join(self.buffer))
            except ValueError:
                pass
            self.active = False


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def date_key(value):
    """Return comparable date components without inventing missing precision."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("date must be an ISO 8601 string or null")
    if re.fullmatch(r"\d{4}", value):
        if not 1 <= int(value) <= 9999:
            raise ValueError("invalid year")
        return (int(value),)
    if re.fullmatch(r"\d{4}-\d{2}", value):
        date.fromisoformat(value + "-01")
        return tuple(map(int, value.split("-")))
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        parsed = date.fromisoformat(value)
        return (parsed.year, parsed.month, parsed.day)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    parsed = parsed.astimezone(timezone.utc)
    return (parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute,
            parsed.second, parsed.microsecond)


def comparable_order(left, right):
    """Compare only mutually known precision, so unknown days stay unknown."""
    precision = min(len(left), len(right))
    return left[:precision] > right[:precision]


class Validator:
    def __init__(self, root: Path, decode: bool = True):
        self.root = root.resolve()
        self.decode = decode
        self.issues = []
        self.tables = {}
        self.documents = {}
        self.ids = {}
        self.checked_media = {}
        self.checked_json = 0
        self.media_hashes = defaultdict(list)
        self.snapshot_cache = {}

    def issue(self, severity, code, path, message):
        self.issues.append({"severity": severity, "code": code,
                            "path": str(path), "message": message})

    def local(self, value):
        if not isinstance(value, str) or not value:
            raise ValueError("local path must be a nonempty relative string")
        normalized = value.replace("\\", "/")
        if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
            raise ValueError("absolute paths are not allowed")
        path = (self.root / normalized).resolve()
        try:
            relative = path.relative_to(self.root)
        except ValueError:
            raise ValueError("path escapes the workspace") from None
        if any(part in BLOCKED_DIRECTORIES for part in relative.parts):
            raise ValueError("path points to an excluded configuration directory")
        return path

    def load(self, relative, expected=None, required=True):
        try:
            path = self.local(relative)
        except ValueError as exc:
            self.issue("error", "unsafe_json_path", relative, str(exc))
            return None
        if not path.exists():
            if required:
                self.issue("error", "missing_json", relative, "Required JSON file is missing.")
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            self.checked_json += 1
        except (OSError, ValueError, UnicodeError) as exc:
            self.issue("error", "invalid_json", relative, str(exc))
            return None
        self.documents[relative] = value
        if expected is not None and not isinstance(value, expected):
            expected_name = " or ".join(t.__name__ for t in expected) if isinstance(expected, tuple) else expected.__name__
            self.issue("error", "invalid_container", relative,
                       f"Expected {expected_name}, received {type(value).__name__}.")
            return None
        return value

    def fields(self, record, required, path):
        missing = sorted(required - record.keys())
        if missing:
            self.issue("error", "missing_fields", path, ", ".join(missing))

    def source_url(self, value):
        if not isinstance(value, str):
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"https", "http"} and bool(parsed.netloc)

    def load_archive(self):
        for name, (path, id_field) in TABLES.items():
            records = self.load(path, list)
            self.tables[name] = records or []
            identifiers = set()
            for index, record in enumerate(records or []):
                pointer = f"{path}#/{index}"
                if not isinstance(record, dict):
                    self.issue("error", "invalid_record", pointer, "Record must be an object.")
                    continue
                if id_field:
                    # timeline_id is accepted for early archive adapters.
                    identifier = record.get(id_field, record.get("timeline_id") if name == "timeline" else None)
                    if not isinstance(identifier, str) or not identifier:
                        self.issue("error", "missing_id", pointer, f"Missing nonempty {id_field}.")
                    elif identifier in identifiers:
                        self.issue("error", "duplicate_id", pointer, identifier)
                    else:
                        identifiers.add(identifier)
            self.ids[name] = identifiers
        self.load("data/raw/page_info.json", dict)
        self.load("data/processed/project_info.json", dict)
        self.load("research/evidence_map.json", (dict, list))
        # Scan only archive JSON, never credentials or repository internals.
        for directory in ("data", "research", "checkpoints"):
            for path in sorted((self.root / directory).rglob("*.json")):
                relative = path.relative_to(self.root).as_posix()
                if not path.is_symlink() and relative not in self.documents:
                    self.load(relative, required=False)

    def relations(self):
        for relative, document in self.documents.items():
            if not relative.startswith("data/") or relative.startswith("data/raw/imports/"):
                continue
            def visit(value, pointer):
                if isinstance(value, dict):
                    for field, item in value.items():
                        target = REFERENCE_TABLES.get(field)
                        here = pointer + "/" + field
                        if target:
                            if not isinstance(item, list):
                                self.issue("error", "invalid_relation", here, "Reference field must be an array.")
                            else:
                                seen = set()
                                for identifier in item:
                                    if not isinstance(identifier, str) or identifier not in self.ids[target]:
                                        self.issue("error", "dangling_reference", here, f"Unknown {target}: {identifier!r}.")
                                    elif identifier in seen:
                                        self.issue("warning", "duplicate_reference", here, identifier)
                                    else:
                                        seen.add(identifier)
                        singular_target = REFERENCE_TABLES.get(field + "s")
                        if singular_target and item is not None:
                            if not isinstance(item, str) or item not in self.ids[singular_target]:
                                self.issue("error", "dangling_reference", here,
                                           f"Unknown {singular_target}: {item!r}.")
                        visit(item, here)
                elif isinstance(value, list):
                    for index, item in enumerate(value):
                        visit(item, f"{pointer}/{index}")
            visit(document, relative + "#")

    def dates(self):
        date_fields = {"published_at", "collected_at", "downloaded_at", "start_date",
                       "end_date", "event_date", "date", "event_start", "event_end"}
        for name, records in self.tables.items():
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                pointer = f"{TABLES[name][0]}#/{index}"
                for field in date_fields & record.keys():
                    try:
                        date_key(record[field])
                    except (ValueError, TypeError) as exc:
                        self.issue("error", "invalid_date", pointer + "/" + field, str(exc))
                for start, end in (("start_date", "end_date"), ("event_start", "event_end")):
                    try:
                        left, right = date_key(record.get(start)), date_key(record.get(end))
                        if left and right and comparable_order(left, right):
                            self.issue("error", "reversed_dates", pointer, f"{start} is after {end}.")
                    except (ValueError, TypeError):
                        pass
        previous = None
        for index, event in enumerate(self.tables["timeline"]):
            if not isinstance(event, dict):
                continue
            value = next((event.get(k) for k in ("event_date", "date", "start_date", "event_start") if event.get(k)), None)
            pointer = f"data/processed/timeline.json#/{index}"
            if value is None:
                self.issue("warning", "timeline_date_unknown", pointer,
                           "Event date is unknown; publication date must not replace it.")
                continue
            try:
                current = date_key(value)
                if previous and comparable_order(previous, current):
                    self.issue("error", "timeline_unsorted", pointer, "Dated events are not in chronological order.")
                previous = current
            except (ValueError, TypeError):
                pass

    def posts(self):
        seen_urls, seen_facebook = set(), set()
        for index, post in enumerate(self.tables["posts"]):
            if not isinstance(post, dict):
                continue
            pointer = f"data/raw/posts.json#/{index}"
            self.fields(post, POST_FIELDS, pointer)
            url = post.get("post_url")
            if not self.source_url(url):
                self.issue("error", "post_source_missing", pointer, "Post must retain a valid direct source URL.")
            elif url in seen_urls:
                self.issue("error", "duplicate_post_url", pointer, url)
            seen_urls.add(url) if isinstance(url, str) else None
            facebook_id = post.get("facebook_post_id")
            if facebook_id:
                if not isinstance(facebook_id, (str, int)):
                    self.issue("error", "invalid_facebook_id", pointer, "Facebook ID must be a string, integer, or null.")
                else:
                    if str(facebook_id) in seen_facebook:
                        self.issue("error", "duplicate_facebook_id", pointer, str(facebook_id))
                    seen_facebook.add(str(facebook_id))
            status, caption = post.get("caption_completeness"), post.get("caption_original")
            if not isinstance(status, str) or status not in CAPTION_STATES:
                self.issue("error", "invalid_caption_status", pointer, "Use complete, partial, or unknown.")
            if caption is not None and not isinstance(caption, str):
                self.issue("error", "invalid_caption", pointer, "Original caption must be a string or null.")
            if status == "complete" and caption is None:
                self.issue("error", "missing_complete_caption", pointer, "A caption marked complete cannot be null.")
            if isinstance(status, str) and status in {"partial", "unknown"}:
                self.issue("warning", "caption_not_proven_complete", pointer,
                           "Original caption completeness is not verified.")
            if not post.get("season_ids"):
                self.issue("warning", "post_season_unknown", pointer, "Post has no verified season assignment.")
            snapshot_verified = self.snapshot_caption_provenance(post, pointer)
            self.caption_provenance(post, pointer, snapshot_verified)

    def snapshot_caption_provenance(self, post, pointer):
        provenance = post.get("provenance")
        evidence = post.get("caption_evidence")
        if evidence is None and isinstance(provenance, dict):
            evidence = provenance.get("caption_evidence")
        if not evidence:
            return False
        if isinstance(evidence, dict):
            evidence = [evidence]
        if not isinstance(evidence, list):
            self.issue("error", "invalid_snapshot_caption_evidence", pointer, "caption_evidence must be an array/object.")
            return False
        verified = False
        for item in evidence:
            if not isinstance(item, dict) or not item.get("snapshot_path"):
                self.issue("error", "invalid_snapshot_caption_evidence", pointer,
                           "Snapshot evidence requires snapshot_path, script_index, and json_path.")
                continue
            try:
                path = self.local(item["snapshot_path"])
                if path not in self.snapshot_cache:
                    parser = SnapshotJSON()
                    parser.feed(path.read_text(encoding="utf-8"))
                    self.snapshot_cache[path] = parser.documents
                value = self.snapshot_cache[path][item["script_index"]]
                expression = item["json_path"]
                if not isinstance(expression, str) or not expression.startswith("$"):
                    raise ValueError("JSON path must start with $")
                brackets = re.findall(r'\[(?:"(?:\\.|[^"\\])*"|\d+)\]', expression[1:])
                if "".join(brackets) != expression[1:]:
                    raise ValueError("Only JSON object keys and array indices are supported")
                for bracket in brackets:
                    token = json.loads(bracket[1:-1])
                    value = value[token]
                if value != post.get("caption_original"):
                    self.issue("error", "snapshot_caption_mismatch", pointer,
                               "Caption differs from the exact message delivered in the saved snapshot.")
                else:
                    verified = True
            except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                self.issue("error", "snapshot_caption_evidence_error", pointer, str(exc))
        return verified

    def caption_provenance(self, post, pointer, snapshot_verified=False):
        provenance = post.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("source_file"):
            if post.get("caption_original") is not None and not snapshot_verified:
                self.issue("warning", "caption_original_source_unavailable", pointer,
                           "No preserved source file is available to compare the original caption.")
            return
        try:
            source = self.local(provenance["source_file"])
            if not source.is_file():
                self.issue("error", "caption_source_missing", pointer, "Preserved caption source file is missing.")
                return
            if provenance.get("source_sha256") != digest(source):
                self.issue("error", "caption_source_hash_mismatch", pointer,
                           "Preserved source hash differs from provenance.")
            if source.suffix.lower() not in {".json", ".jsonl"}:
                if not snapshot_verified:
                    self.issue("warning", "caption_source_pointer_unknown", pointer,
                               "Preserved non-JSON source needs snapshot caption evidence to compare the original text.")
                return
            document = json.loads(source.read_text(encoding="utf-8-sig"))
            location = provenance.get("json_pointer", "")
            entry = None
            if isinstance(location, str) and re.fullmatch(r"entry/\d+", location):
                entries = document
                if isinstance(document, dict):
                    entries = next((document[k] for k in ("your_posts_v2", "posts_v2", "posts")
                                    if isinstance(document.get(k), list)), None)
                if isinstance(entries, list):
                    entry = entries[int(location.split("/")[1])]
            elif isinstance(location, str) and location.startswith("/"):
                entry = document
                for part in location[1:].split("/"):
                    part = part.replace("~1", "/").replace("~0", "~")
                    entry = entry[int(part)] if isinstance(entry, list) else entry[part]
            field = provenance.get("caption_field")
            if isinstance(entry, dict) and field in ("caption_original", "post", "message"):
                original = entry.get(field)
            elif isinstance(entry, dict) and field == "data[*].post":
                parts = [item["post"] for item in entry.get("data", [])
                         if isinstance(item, dict) and isinstance(item.get("post"), str)]
                original = "\n".join(parts) if parts else None
            elif field is None and post.get("caption_original") is None:
                return
            else:
                self.issue("warning", "caption_source_pointer_unknown", pointer,
                           "Source is preserved, but this caption pointer cannot be independently resolved.")
                return
            if original != post.get("caption_original"):
                self.issue("error", "caption_original_mismatch", pointer,
                           "Original caption differs from the preserved export, including Unicode/newlines.")
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            self.issue("error", "caption_provenance_error", pointer, str(exc))

    def seasons(self):
        for index, season in enumerate(self.tables["seasons"]):
            if not isinstance(season, dict):
                continue
            pointer = f"data/processed/seasons.json#/{index}"
            self.fields(season, SEASON_FIELDS, pointer)
            number = season.get("season_number")
            if number is not None and (type(number) is not int or number < 1):
                self.issue("error", "invalid_season_number", pointer, "Season number must be a positive integer or null.")
            status = season.get("verification_status")
            if not isinstance(status, str) or status not in VERIFICATION:
                self.issue("error", "invalid_verification_status", pointer, "Use verified, inferred, or unknown.")
            urls = season.get("source_urls", [])
            if not isinstance(urls, list):
                self.issue("error", "invalid_source_urls", pointer, "source_urls must be an array.")
                urls = []
            if status == "verified" and not any(self.source_url(x) for x in urls):
                self.issue("error", "season_evidence_missing", pointer, "Verified season needs a direct source URL.")
            if status != "verified":
                self.issue("warning", "season_not_verified", pointer, "Season existence or attribution needs verification.")
            if status == "verified" and not season.get("evidence_ids") and not season.get("evidence"):
                self.issue("warning", "season_evidence_link_review", pointer,
                           "Review the evidence map and confirm that sources explicitly identify this season.")

    def season_bundles(self):
        for season in self.tables["seasons"]:
            if not isinstance(season, dict) or season.get("verification_status") != "verified":
                continue
            season_id = season.get("season_id")
            if not isinstance(season_id, str) or not season_id:
                continue
            folder = season.get("season_directory", f"data/seasons/{season_id}")
            try:
                directory = self.local(folder)
            except ValueError as exc:
                self.issue("error", "unsafe_season_directory", str(folder), str(exc))
                continue
            for filename in ("season_info.json", "posts.json", "programs.json", "journeys.json", "timeline.json", "media_manifest.json"):
                relative = (directory / filename).relative_to(self.root).as_posix()
                value = self.documents.get(relative)
                if value is None:
                    self.issue("error", "missing_season_file", relative,
                               "A verified season requires its own documented data bundle.")
                    continue
                expected = dict if filename == "season_info.json" else list
                if not isinstance(value, expected):
                    self.issue("error", "invalid_season_container", relative,
                               f"Expected {expected.__name__}.")
                    continue
                if filename == "season_info.json":
                    if value.get("season_id") != season_id:
                        self.issue("error", "season_bundle_id_mismatch", relative,
                                   "season_info ID differs from the global season record.")
                elif filename in ("posts.json", "programs.json", "journeys.json"):
                    name = filename[:-5]
                    id_field = TABLES[name][1]
                    actual = {x.get(id_field) for x in value if isinstance(x, dict) and isinstance(x.get(id_field), str)}
                    links = season.get(id_field + "s", [])
                    expected_ids = set(links) if isinstance(links, list) and all(isinstance(x, str) for x in links) else set()
                    if actual != expected_ids:
                        self.issue("error", "season_bundle_relation_mismatch", relative,
                                   f"IDs differ from the season's {id_field}s links.")
            for filename in ("season_story.md", "sources.md"):
                path = directory / filename
                relative = path.relative_to(self.root).as_posix()
                if not path.is_file() or path.stat().st_size == 0:
                    self.issue("error", "missing_season_document", relative,
                               "Verified season needs a nonempty story/limitations document and source list.")

    def inspect_media(self, record, pointer):
        local_path = record.get("local_path")
        stored = bool(local_path)
        if isinstance(record.get("download_status"), str) and record["download_status"] in LOCAL_STATES and not stored:
            self.issue("error", "media_path_missing", pointer, "Successful/local import status requires a local file.")
        if not stored:
            return False
        try:
            path = self.local(local_path)
        except ValueError as exc:
            self.issue("error", "unsafe_path", pointer, str(exc))
            return False
        if not path.is_file():
            self.issue("error", "media_file_missing", pointer, str(local_path))
            return False
        if path not in self.checked_media:
            probe = None
            try:
                actual = digest(path)
            except OSError as exc:
                self.issue("error", "media_read_error", pointer, str(exc))
                return False
            self.media_hashes[actual].append(local_path)
            if shutil.which("ffprobe"):
                try:
                    process = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,codec_name", "-of", "json", str(path)],
                        capture_output=True, text=True, timeout=90)
                    if process.returncode:
                        self.issue("error", "media_unreadable", pointer, "ffprobe cannot read the media file.")
                    else:
                        streams = json.loads(process.stdout).get("streams", [])
                        probe = streams[0] if streams else None
                except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
                    self.issue("error", "media_probe_error", pointer, str(exc))
            else:
                self.issue("warning", "media_probe_unavailable", pointer, "ffprobe is unavailable.")
            if self.decode and shutil.which("ffmpeg"):
                # A complete decode checks for damaged image/video data; no output is retained.
                try:
                    process = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path),
                        "-f", "null", "-"], capture_output=True, text=True, timeout=180)
                    if process.returncode:
                        self.issue("error", "media_decode_failed", pointer, "ffmpeg reported a damaged or unsupported media file.")
                except (OSError, subprocess.TimeoutExpired) as exc:
                    self.issue("error", "media_decode_error", pointer, str(exc))
            elif self.decode:
                self.issue("warning", "media_decode_unavailable", pointer, "ffmpeg is unavailable; full decode was not tested.")
            self.checked_media[path] = {"sha256": actual, "file_size": path.stat().st_size, "probe": probe}
        metadata = self.checked_media[path]
        if not isinstance(record.get("sha256"), str) or record["sha256"] != metadata["sha256"]:
            self.issue("error", "media_hash_mismatch", pointer, "Stored sha256 does not match the file.")
        if record.get("file_size") != metadata["file_size"]:
            self.issue("error", "media_size_mismatch", pointer, "Stored file_size does not match the file.")
        if metadata["probe"]:
            for field in ("width", "height"):
                if record.get(field) is not None and record[field] != metadata["probe"].get(field):
                    self.issue("error", "media_dimensions_mismatch", pointer, f"Stored {field} does not match the file.")
        return True

    def media(self):
        for name in ("photos", "videos"):
            for index, media in enumerate(self.tables[name]):
                if not isinstance(media, dict):
                    continue
                pointer = f"{TABLES[name][0]}#/{index}"
                if name == "photos":
                    self.fields(media, PHOTO_FIELDS, pointer)
                self.inspect_media(media, pointer)
                if not isinstance(media.get("rights_status"), str) or media["rights_status"] not in RIGHTS_STATES:
                    self.issue("error", "invalid_rights_status", pointer, "Media needs an explicit rights status.")
                if type(media.get("privacy_review_required")) is not bool:
                    self.issue("error", "missing_privacy_review_flag", pointer, "Media needs a boolean privacy_review_required flag.")
                if isinstance(media.get("rights_status"), str) and media["rights_status"] in {"unknown", "restricted"}:
                    self.issue("warning", "media_rights_unresolved", pointer, "Media is not cleared for independent website publication.")
                if media.get("rights_status") in ("permission_confirmed", "owned", "licensed") and not media.get("rights_evidence"):
                    self.issue("error", "media_rights_evidence_missing", pointer,
                               "Confirmed rights status requires preserved permission/license/ownership evidence.")
                if media.get("publication_status") in ("published", "approved", "public"):
                    if media.get("rights_status") not in ("permission_confirmed", "owned", "licensed"):
                        self.issue("error", "media_publication_without_rights", pointer,
                                   "Media marked public/approved has unresolved publication rights.")
                    if media.get("privacy_review_required") is not False:
                        self.issue("error", "media_publication_before_privacy_review", pointer,
                                   "Media marked public/approved still requires privacy review.")
                if not media.get("post_ids") and not media.get("source_post_ids"):
                    self.issue("warning", "media_without_post", pointer, "Media is not linked to an archived post.")
        for index, record in enumerate(self.tables["media_index"]):
            if not isinstance(record, dict):
                continue
            pointer = f"data/processed/media_index.json#/{index}"
            identifier = record.get("media_id")
            kind = record.get("media_type")
            target = {"photo": "photos", "image": "photos", "video": "videos"}.get(kind) if isinstance(kind, str) else None
            if not target or not isinstance(identifier, str) or identifier not in self.ids[target]:
                self.issue("error", "invalid_media_index_reference", pointer,
                           "Media index needs a media_id and media_type matching an archived photo/video.")
            if record.get("local_path"):
                self.inspect_media(record, pointer)
        for file_hash, paths in self.media_hashes.items():
            if len(paths) > 1:
                self.issue("warning", "duplicate_media_bytes", "data/raw", f"{file_hash}: {paths}")

    def inventory(self):
        inventory = self.documents.get("research/environment_inventory.json", {})
        if not isinstance(inventory, dict):
            return
        for entry in inventory.get("files", []):
            if not isinstance(entry, dict) or not entry.get("sha256"):
                continue
            try:
                path = self.local(entry.get("path"))
                if not path.is_file() or digest(path) != entry["sha256"]:
                    self.issue("error", "initial_file_modified", entry.get("path"), "Initial workspace file is missing or changed.")
            except (ValueError, OSError) as exc:
                self.issue("error", "inventory_file_error", str(entry.get("path")), str(exc))

    def counts(self):
        def rows(name):
            return [x for x in self.tables[name] if isinstance(x, dict)]
        posts, photos, videos = rows("posts"), rows("photos"), rows("videos")
        def local_exists(record):
            try:
                return bool(record.get("local_path")) and self.local(record["local_path"]).is_file()
            except ValueError:
                return False
        discovered = rows("discovered_urls")
        return {
            "json_files_checked": self.checked_json,
            "discovered_url_records": len(discovered),
            "posts_archived": len(posts),
            "posts_with_caption_complete": sum(p.get("caption_completeness") == "complete" for p in posts),
            "posts_with_caption_partial": sum(p.get("caption_completeness") == "partial" for p in posts),
            "posts_with_caption_unknown": sum(p.get("caption_completeness") == "unknown" for p in posts),
            "posts_without_season": sum(not p.get("season_ids") for p in posts),
            "photo_metadata_records": len(photos),
            "photos_with_local_file": sum(local_exists(p) for p in photos),
            "photos_imported_from_workspace": sum(local_exists(p) and p.get("download_status") in ("local_imported", "imported") for p in photos),
            "photos_downloaded_from_remote": sum(local_exists(p) and p.get("download_status") in ("downloaded", "success") for p in photos),
            "photo_download_failures": sum(p.get("download_status") in ("error", "failed", "download_failed") for p in photos),
            "videos_metadata_records": len(videos),
            "videos_with_local_file": sum(local_exists(p) for p in videos),
            "unique_local_media_files_checked": len(self.checked_media),
            "seasons_discovered": len(rows("seasons")),
            "seasons_verified": sum(s.get("verification_status") == "verified" for s in rows("seasons")),
            "programs": len(rows("programs")),
            "programs_verified": sum(p.get("verification_status") == "verified" for p in rows("programs")),
            "journeys": len(rows("journeys")),
            "timeline_events": len(rows("timeline")),
            "milestones": len(rows("milestones")),
            "stories": len(rows("stories")),
            "total_facebook_posts": None,
            "facebook_history_completion_percent": None,
        }

    def run(self):
        self.load_archive()
        self.relations()
        self.dates()
        self.posts()
        self.seasons()
        self.season_bundles()
        self.media()
        self.inventory()
        if not self.tables["posts"]:
            self.issue("warning", "no_posts_archived", "data/raw/posts.json",
                       "No Facebook post captions have been archived; historical coverage is incomplete.")
        if not self.tables["seasons"]:
            self.issue("warning", "no_verified_season_inventory", "data/processed/seasons.json",
                       "No season record has been established from the accessible evidence.")
        severity = Counter(x["severity"] for x in self.issues)
        return {
            "schema_version": "1.0",
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "integrity_status": "failed" if severity["error"] else "passed_with_warnings" if severity["warning"] else "passed",
            "scope": "Offline archive integrity only; this does not certify complete historical coverage or publication approval.",
            "counts": self.counts(),
            "issue_counts": {"error": severity["error"], "warning": severity["warning"]},
            "issues": self.issues,
            "checks": ["UTF-8 JSON and containers", "unique IDs and references", "ISO dates and timeline order",
                       "caption completeness flags", "season sources and unknown facts", "local media hashes and byte sizes",
                       "media dimensions and decoding", "rights and privacy flags", "initial source file preservation"],
            "limits": ["Cannot prove caption completeness without a complete original source/export.",
                       "Cannot establish total Facebook posts or complete seasonal coverage from a blocked source.",
                       "Source URLs and season labels require human/source-content review; URL presence alone does not prove a claim.",
                       "Rights flags are metadata, not evidence of legal permission."],
        }


def write_reports(report, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = report["counts"]
    lines = ["# Báo cáo chất lượng dữ liệu", "", f"Thời điểm kiểm tra (UTC): {report['validated_at']}", "",
             f"Kết quả kiểm tra kỹ thuật: `{report['integrity_status']}`.", "",
             "Kết quả này kiểm tra tính nhất quán của dữ liệu hiện có; không xác nhận đã thu thập đầy đủ lịch sử Facebook hoặc được phép công bố media.", "",
             "| Chỉ số | Số lượng |", "|---|---:|"]
    labels = {"json_files_checked": "File JSON đã kiểm tra", "discovered_url_records": "Bản ghi URL phát hiện",
              "posts_archived": "Bài đăng đã lưu", "posts_with_caption_complete": "Caption được đánh dấu đầy đủ",
              "posts_with_caption_partial": "Caption bị thiếu một phần", "posts_with_caption_unknown": "Caption chưa rõ độ đầy đủ",
              "posts_without_season": "Bài chưa xác định mùa", "photo_metadata_records": "Hồ sơ ảnh",
              "photos_with_local_file": "Ảnh có file thực tế", "photos_imported_from_workspace": "Ảnh nhập từ workspace có sẵn",
              "photos_downloaded_from_remote": "Ảnh tải từ nguồn từ xa", "photo_download_failures": "Ảnh tải lỗi",
              "videos_metadata_records": "Hồ sơ video", "videos_with_local_file": "Video có file thực tế",
              "seasons_discovered": "Hồ sơ mùa", "seasons_verified": "Mùa đã xác minh", "programs": "Chương trình",
              "programs_verified": "Chương trình đã xác minh", "journeys": "Chuyến đi", "timeline_events": "Sự kiện timeline",
              "milestones": "Dấu mốc", "stories": "Câu chuyện"}
    lines += [f"| {label} | {count[key]} |" for key, label in labels.items()]
    lines += ["", f"Lỗi: {report['issue_counts']['error']}. Cảnh báo: {report['issue_counts']['warning']}.", "",
              "Không biết tổng số bài đăng thực tế trên Facebook; không tính tỷ lệ hoàn chỉnh.", "",
              "Các giới hạn kiểm tra: caption chỉ được coi là đầy đủ theo trạng thái trong hồ sơ, cần đối chiếu bản gốc; URL nguồn không tự chứng minh nội dung của khẳng định; quyền sử dụng và quyền riêng tư cần được duyệt trước khi xuất bản.", ""]
    if report["issues"]:
        lines += ["| Mức | Mã | Vị trí | Nội dung |", "|---|---|---|---|"]
        for issue in report["issues"]:
            values = [str(issue[key]).replace("|", "\\|").replace("\n", " ") for key in ("severity", "code", "path", "message")]
            lines.append("| " + " | ".join(values) + " |")
    lines += ["", "Chi tiết có thể đọc bằng máy được lưu trong `reports/validation.json`.", ""]
    (output / "DATA_QUALITY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--report-dir", type=Path, help="Defaults to <root>/reports.")
    parser.add_argument("--skip-decode", action="store_true", help="Skip full ffmpeg decoding; hashes and metadata are still checked.")
    args = parser.parse_args()
    validator = Validator(args.root, decode=not args.skip_decode)
    report = validator.run()
    write_reports(report, args.report_dir or args.root / "reports")
    print(json.dumps({"integrity_status": report["integrity_status"], "issue_counts": report["issue_counts"],
                      "counts": report["counts"]}, ensure_ascii=False, indent=2))
    return 1 if report["issue_counts"]["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
