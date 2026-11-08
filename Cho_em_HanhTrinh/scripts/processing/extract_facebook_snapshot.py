#!/usr/bin/env python3
"""Extract evidence already delivered in a saved public Facebook HTML snapshot.

Offline only: this module performs no requests and never executes page JavaScript.
It reads application/json script blocks, retains exact delivered message.text,
and records JSON paths so every extracted value can be checked against the HTML.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo


class SnapshotParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.script_index = -1
        self.json_script = False
        self.buffer = []
        self.documents = []
        self.errors = []
        self.links = []
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self.script_index += 1
            self.json_script = attrs.get("type", "").lower() == "application/json"
            self.buffer = []
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        elif tag == "meta" and attrs.get("content"):
            name = attrs.get("property") or attrs.get("name")
            if name and name.startswith(("og:", "description", "twitter:")):
                self.meta[name] = attrs["content"]

    def handle_data(self, data):
        if self.json_script:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.json_script:
            try:
                self.documents.append((self.script_index, json.loads("".join(self.buffer))))
            except json.JSONDecodeError as exc:
                self.errors.append({"script_index": self.script_index, "error": str(exc)})
            self.json_script = False


class Element:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs or []), parent
        self.children = []

    def descendants(self):
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.descendants()

    def text(self):
        if self.tag in ("script", "style"):
            return ""
        if self.tag == "img":
            return self.attrs.get("alt", "")
        body = "".join(c.text() if isinstance(c, Element) else c for c in self.children)
        return body + ("\n" if self.tag in ("div", "p", "br", "h2", "h3") else "")


class DOMParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("root")
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent and node.tag != tag:
            node = node.parent
        if node.parent:
            self.current = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def canonical_observed_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    for key in list(query):
        if key.startswith("__"):
            del query[key]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True), fragment=""))


def extract_dom(html, snapshot_path):
    """Keep lazy-loaded visible excerpts separate from exact JSON messages."""
    parser = DOMParser()
    parser.feed(html)
    articles = []
    for article in parser.root.descendants():
        if article.attrs.get("role") != "article" or not article.attrs.get("aria-posinset"):
            continue
        elements = list(article.descendants())
        messages = [e for e in elements if e.attrs.get("data-ad-preview") == "message"]
        if not messages:
            continue
        caption = re.sub(r"\n{3,}", "\n\n", messages[0].text()).strip()
        links = [(e, e.attrs["href"]) for e in elements if e.tag == "a" and e.attrs.get("href")]
        post_links, photo_nodes, author_links, video_links, album_post_ids = [], [], [], [], []
        timestamp_labels = []
        for element, url in links:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            if "facebook.com" in parsed.netloc and ("story_fbid" in query or "/posts/" in parsed.path) and "comment_id" not in query:
                canonical = canonical_observed_url(url)
                unique_append(post_links, canonical)
                label = element.text().strip()
                if label:
                    unique_append(timestamp_labels, label)
            if "facebook.com" in parsed.netloc and any(part in parsed.path for part in ("/reel/", "/videos/")) and "comment_id" not in query:
                unique_append(video_links, canonical_observed_url(url))
                label = element.text().strip()
                if label and re.search(r"Tháng|tháng|ngày|tuần|giờ", label):
                    unique_append(timestamp_labels, label)
            if "facebook.com" in parsed.netloc and ("/people/CHO-EM-project/" in parsed.path or query.get("id") == ["100094610840245"]):
                if "story_fbid" not in query:
                    unique_append(author_links, canonical_observed_url(url))
            photo_ids = query.get("fbid", []) if "photo" in parsed.path else []
            for photo_id in photo_ids:
                for photo_set in query.get("set", []):
                    match = re.fullmatch(r"pcb\.(\d+)", photo_set)
                    if match:
                        unique_append(album_post_ids, match.group(1))
                images = [e for e in element.descendants() if e.tag == "img" and e.attrs.get("src")]
                photo = next((p for p in photo_nodes if p["facebook_photo_id"] == photo_id), None)
                if photo is None:
                    photo = {"facebook_photo_id": photo_id, "photo_page_url": canonical_observed_url(url), "image_elements": []}
                    photo_nodes.append(photo)
                for image in images:
                    unique_append(photo["image_elements"], {"src": image.attrs["src"], "alt": image.attrs.get("alt"),
                                                           "rendered_width": image.attrs.get("width"), "rendered_height": image.attrs.get("height")})
        videos = [e for e in elements if e.tag == "video"]
        all_text = article.text()
        duration_labels = re.findall(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", all_text)
        selector = '[role="article"][aria-posinset="' + article.attrs["aria-posinset"] + '"]'
        fingerprint = hashlib.sha256((caption + "\n" + "|".join(timestamp_labels)).encode()).hexdigest()[:20]
        articles.append({"discovery_id": "dom_" + fingerprint, "source_status": "direct_public_dom_excerpt",
                         "caption_visible_excerpt": caption, "caption_original": None,
                         "caption_status": "visible_excerpt_only" if "Xem thêm" in caption else "visible_dom_text_completeness_unconfirmed",
                         "post_urls": post_links, "author_profile_urls": author_links,
                         "video_urls": video_links, "facebook_post_ids_from_observed_photo_set": album_post_ids,
                         "published_at": None, "visible_timestamp_labels": timestamp_labels,
                         "photos": photo_nodes,
                         "video_elements": [{"src": e.attrs.get("src"), "poster": e.attrs.get("poster"),
                                             "note": "Blob src is session-local and is not a downloadable archive source."} for e in videos],
                         "video_duration_visible_labels": list(dict.fromkeys(duration_labels)),
                         "season_numbers_visible": list(dict.fromkeys(re.findall(r"mùa\s+(\d+)\b", caption, re.I))),
                         "evidence": {"snapshot_path": str(snapshot_path), "dom_selector": selector}})
    return articles


def walk(value, path="$"):
    """Yield dictionaries and unambiguous paths within one JSON script."""
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + "[" + json.dumps(key, ensure_ascii=False) + "]")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + f"[{index}]")


def unique_append(items, value):
    if value not in items:
        items.append(value)


def extract(input_path: Path, metadata_path: Path | None = None):
    raw = input_path.read_bytes()
    parser = SnapshotParser()
    parser.feed(raw.decode("utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path and metadata_path.exists() else {}
    collected_at = metadata.get("collected_at")
    if not collected_at:
        for snap in metadata.get("snapshots", []):
            if isinstance(snap, dict) and any(str(value).endswith(input_path.name) for value in snap.values()):
                collected_at = snap.get("collected_at") or snap.get("timestamp")
        collected_at = collected_at or metadata.get("updated_at") or metadata.get("finished_at")
    source_url = metadata.get("source_url") or metadata.get("final_url")
    posts, photos, profiles = {}, {}, {}
    nodes = []
    for script_index, doc in parser.documents:
        nodes.extend((script_index, path, node) for path, node in walk(doc))

    def evidence(index, path):
        return {"snapshot_path": str(input_path), "script_index": index, "json_path": path}

    for index, path, node in nodes:
        post_id = node.get("post_id")
        if post_id and any(key in node for key in ("creation_time", "actors", "message", "comet_sections")):
            post_id = str(post_id)
            post = posts.setdefault(post_id, {
                "facebook_post_id": post_id, "source_status": "direct_public_snapshot_json",
                "collected_at": collected_at, "source_urls": [], "actor_ids": [],
                "creation_times": [], "caption_variants": [], "photo_ids": [],
                "attachment_counts": [], "evidence": [],
            })
            unique_append(post["evidence"], evidence(index, path))
            for subpath, child in walk(node, path):
                for urlkey in ("permalink_url", "wwwURL", "url"):
                    url = child.get(urlkey)
                    if isinstance(url, str) and "facebook.com/" in url and (
                        "story_fbid=" in url or "/posts/" in url
                    ) and "comment_id=" not in url:
                        unique_append(post["source_urls"], url)
                if child.get("creation_time"):
                    item = {"unix": child["creation_time"], "evidence": evidence(index, subpath + '["creation_time"]')}
                    unique_append(post["creation_times"], item)
                for actor in child.get("actors", []) if isinstance(child.get("actors"), list) else []:
                    if isinstance(actor, dict) and actor.get("id"):
                        unique_append(post["actor_ids"], str(actor["id"]))
                message = child.get("message")
                if isinstance(message, dict) and isinstance(message.get("text"), str) and message["text"]:
                    text = message["text"]
                    variant = next((v for v in post["caption_variants"] if v["text"] == text), None)
                    if variant is None:
                        variant = {"text": text, "evidence": []}
                        post["caption_variants"].append(variant)
                    unique_append(variant["evidence"], evidence(index, subpath + '["message"]["text"]'))
                if child.get("__typename") == "Photo" and child.get("id"):
                    unique_append(post["photo_ids"], str(child["id"]))
                subattachments = child.get("all_subattachments")
                if isinstance(subattachments, dict) and subattachments.get("count") is not None:
                    item = {"reported_count": subattachments["count"], "delivered_node_count": len(subattachments.get("nodes", [])),
                            "evidence": evidence(index, subpath + '["all_subattachments"]')}
                    unique_append(post["attachment_counts"], item)

        if node.get("__typename") == "Photo" and node.get("id"):
            photo_id = str(node["id"])
            photo = photos.setdefault(photo_id, {"facebook_photo_id": photo_id, "owner_ids": [], "image_variants": [],
                                                "accessibility_captions": [], "observed_photo_page_urls": [], "source_post_ids": [], "evidence": []})
            unique_append(photo["evidence"], evidence(index, path))
            owner = node.get("owner")
            if isinstance(owner, dict) and owner.get("id"):
                unique_append(photo["owner_ids"], str(owner["id"]))
            for field in ("image", "viewer_image", "large_share_image", "thumbnailImage"):
                img = node.get(field)
                if isinstance(img, dict) and (img.get("uri") or img.get("url")):
                    uri = img.get("uri") or img.get("url")
                    variant = next((v for v in photo["image_variants"] if v["uri"] == uri), None)
                    if variant is None:
                        variant = {"uri": uri, "width": img.get("width"), "height": img.get("height"), "fields": [], "evidence": []}
                        photo["image_variants"].append(variant)
                    unique_append(variant["fields"], field)
                    unique_append(variant["evidence"], evidence(index, path + '["' + field + '"]'))
            if node.get("accessibility_caption"):
                unique_append(photo["accessibility_captions"], {"text": node["accessibility_caption"], "machine_generated": True,
                                                                "evidence": evidence(index, path + '["accessibility_caption"]')})

        if node.get("name") == "CHO EM project" and node.get("id"):
            profile_id = str(node["id"])
            profile = profiles.setdefault(profile_id, {"id": profile_id, "name": node["name"], "observed_fields": {}, "evidence": []})
            unique_append(profile["evidence"], evidence(index, path))
            for key in ("url", "profile_url", "username_for_profile", "category_name", "best_description", "is_additional_profile_plus"):
                if key in node and node[key] is not None:
                    unique_append(profile["observed_fields"].setdefault(key, []), {"value": node[key], "evidence": evidence(index, path + '["' + key + '"]')})

    for link in parser.links:
        parsed = urlparse(link)
        if parsed.hostname and (parsed.hostname == "facebook.com" or parsed.hostname.endswith(".facebook.com")):
            ids = parse_qs(parsed.query).get("fbid", [])
            for photo_id in ids:
                if photo_id in photos and "photo" in parsed.path:
                    unique_append(photos[photo_id]["observed_photo_page_urls"], link)

    season_mentions, date_mentions = [], []
    for post in posts.values():
        post["post_url"] = post["source_urls"][0] if post["source_urls"] else None
        creation = post["creation_times"][0]["unix"] if post["creation_times"] else None
        post["published_at"] = datetime.fromtimestamp(creation, timezone.utc).isoformat() if isinstance(creation, (int, float)) else None
        post["published_at_asia_bangkok"] = datetime.fromtimestamp(creation, ZoneInfo("Asia/Bangkok")).isoformat() if isinstance(creation, (int, float)) else None
        caption = max(post["caption_variants"], key=lambda item: len(item["text"]), default=None)
        post["caption_original"] = caption["text"] if caption else None
        post["caption_evidence"] = caption["evidence"] if caption else []
        post["caption_status"] = "exact_message_text_as_delivered_in_snapshot" if caption else "not_delivered"
        post["caption_character_count"] = len(post["caption_original"]) if caption else 0
        post["caption_clean"] = unicodedata.normalize("NFKC", post["caption_original"]) if caption else None
        post["hashtags"] = re.findall(r"(?<!\w)#[\w]+", post["caption_original"] or "", re.UNICODE)
        for photo_id in post["photo_ids"]:
            if photo_id in photos:
                unique_append(photos[photo_id]["source_post_ids"], post["facebook_post_id"])
        if caption:
            for match in re.finditer(r"mùa\s+(\d+|[IVX]+)\b", caption["text"], re.I):
                season_mentions.append({"facebook_post_id": post["facebook_post_id"], "text": match.group(0),
                                        "number_text": match.group(1), "caption_offset": [match.start(), match.end()],
                                        "evidence": caption["evidence"], "source_status": "direct_public_snapshot_json"})
            for match in re.finditer(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)", caption["text"]):
                date_mentions.append({"facebook_post_id": post["facebook_post_id"], "text": match.group(0),
                                      "caption_offset": [match.start(), match.end()], "evidence": caption["evidence"],
                                      "note": "Date mentioned in caption; distinct from post publication timestamp."})

    return {
        "schema_version": 1, "method": "offline_public_snapshot_json_extraction", "network_requests": 0,
        "source_snapshot": str(input_path), "source_metadata": str(metadata_path) if metadata_path else None,
        "source_url": source_url, "collected_at": collected_at,
        "extracted_at": datetime.now(timezone.utc).isoformat(), "sha256": hashlib.sha256(raw).hexdigest(),
        "script_count": parser.script_index + 1, "parsed_json_script_count": len(parser.documents), "json_parse_errors": parser.errors,
        "page_meta": parser.meta, "profile_records": list(profiles.values()), "posts": list(posts.values()), "photos": list(photos.values()),
        "dom_post_discoveries": extract_dom(raw.decode("utf-8"), input_path),
        "season_mentions": season_mentions, "date_mentions": date_mentions,
        "counts": {"posts": len(posts), "photos_with_metadata_or_id": len(photos),
                   "photos_with_image_urls": sum(bool(p["image_variants"]) for p in photos.values()),
                   "distinct_season_numbers_mentioned": sorted({m["number_text"] for m in season_mentions})},
        "limitations": ["Only data already delivered in this saved HTML is extracted.",
                        "Reported album counts do not mean every attachment was delivered or downloaded.",
                        "No unseen seasons, dates, images or captions are synthesized.",
                        "Image URL access and reuse rights require separate checks; no media is downloaded by this script.",
                        "Accessibility captions may be machine generated and do not establish identity or consent."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, action="append", help="Repeat to merge snapshots without duplicate records.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata", type=Path, action="append", help="One metadata file per input, in matching order.")
    parser.add_argument("--media-manifest", type=Path, help="Optional deduplicated image download manifest; no files are downloaded.")
    args = parser.parse_args()
    metadatas = args.metadata or []
    if metadatas and len(metadatas) != len(args.input):
        parser.error("Provide one --metadata for each --input, or omit metadata.")
    results = [extract(path, metadatas[i] if metadatas else None) for i, path in enumerate(args.input)]
    result = json.loads(json.dumps(results[0]))
    if len(results) > 1:
        result["source_snapshots"] = [{key: r[key] for key in ("source_snapshot", "source_metadata", "source_url", "collected_at", "sha256", "parsed_json_script_count")} for r in results]
        def merge_records(key, identity):
            merged = {}
            for source in results:
                for record in source[key]:
                    record_id = identity(record)
                    if record_id not in merged:
                        merged[record_id] = json.loads(json.dumps(record))
                    else:
                        target = merged[record_id]
                        for field, values in record.items():
                            if isinstance(values, list):
                                for value in values:
                                    unique_append(target.setdefault(field, []), value)
                    if key == "dom_post_discoveries":
                        unique_append(merged[record_id].setdefault("source_evidence", []), record["evidence"])
            return list(merged.values())
        result["posts"] = merge_records("posts", lambda x: x["facebook_post_id"])
        result["photos"] = merge_records("photos", lambda x: x["facebook_photo_id"])
        result["profile_records"] = merge_records("profile_records", lambda x: x["id"])
        result["dom_post_discoveries"] = merge_records("dom_post_discoveries", lambda x: x["post_urls"][0] if x["post_urls"] else x["discovery_id"])
        for key in ("season_mentions", "date_mentions"):
            result[key] = []
            for source in results:
                for item in source[key]:
                    unique_append(result[key], item)
        result["counts"] = {"posts": len(result["posts"]), "photos_with_metadata_or_id": len(result["photos"]),
                            "photos_with_image_urls": sum(bool(p["image_variants"]) for p in result["photos"]),
                            "dom_post_discoveries": len(result["dom_post_discoveries"]),
                            "dom_discoveries_with_post_urls": sum(bool(p["post_urls"]) for p in result["dom_post_discoveries"]),
                            "distinct_season_numbers_mentioned": sorted({m["number_text"] for m in result["season_mentions"]})}
    result["related_page_records"] = [p for p in result["profile_records"] if p["id"] != "100094610840245"]
    for related in result["related_page_records"]:
        related["relationship_note"] = "Observed as user.delegate_page in source JSON; distinct from the public-facing owner profile ID."
    result["profile_records"] = [p for p in result["profile_records"] if p["id"] == "100094610840245"]
    photo_map = {p["facebook_photo_id"]: p for p in result["photos"]}
    for post in result["dom_post_discoveries"]:
        merged_photos = {}
        for photo in post["photos"]:
            photo_id = photo["facebook_photo_id"]
            if photo_id not in merged_photos:
                merged_photos[photo_id] = json.loads(json.dumps(photo))
            else:
                for element in photo["image_elements"]:
                    unique_append(merged_photos[photo_id]["image_elements"], element)
        post["photos"] = list(merged_photos.values())
        for dom_photo in post["photos"]:
            photo_id = dom_photo["facebook_photo_id"]
            photo = photo_map.setdefault(photo_id, {"facebook_photo_id": photo_id, "owner_ids": [], "image_variants": [],
                                                   "accessibility_captions": [], "observed_photo_page_urls": [], "source_post_ids": [], "evidence": []})
            unique_append(photo["observed_photo_page_urls"], dom_photo["photo_page_url"])
            for evidence in post.get("source_evidence", [post["evidence"]]):
                unique_append(photo["evidence"], evidence)
            for post_id in post["facebook_post_ids_from_observed_photo_set"]:
                unique_append(photo["source_post_ids"], post_id)
            for image in dom_photo["image_elements"]:
                variant = {"uri": image["src"], "width": None, "height": None, "fields": ["DOM img.src"],
                           "rendered_width": image["rendered_width"], "rendered_height": image["rendered_height"],
                           "evidence": post.get("source_evidence", [post["evidence"]])}
                unique_append(photo["image_variants"], variant)
    result["photos"] = list(photo_map.values())
    manifest = []
    for photo in result["photos"]:
        variants = {}
        for variant in photo["image_variants"]:
            if variant["uri"] not in variants:
                variants[variant["uri"]] = json.loads(json.dumps(variant))
            else:
                for ev in variant["evidence"]:
                    unique_append(variants[variant["uri"]]["evidence"], ev)
        photo["image_variants"] = list(variants.values())
        if not photo["image_variants"]:
            continue
        best = max(photo["image_variants"], key=lambda v: (v.get("width") or 0) * (v.get("height") or 0))
        post_urls = []
        for post in result["posts"]:
            if photo["facebook_photo_id"] in post["photo_ids"]:
                unique_append(post_urls, post["post_url"])
        for post in result["dom_post_discoveries"]:
            if any(p["facebook_photo_id"] == photo["facebook_photo_id"] for p in post["photos"]):
                for url in post["post_urls"]:
                    unique_append(post_urls, url)
        manifest.append({"photo_id": photo["facebook_photo_id"], "facebook_photo_id": photo["facebook_photo_id"],
                         "source_url": best["uri"], "source_post_url": post_urls[0] if post_urls else None,
                         "source_post_urls": post_urls, "source_photo_urls": photo["observed_photo_page_urls"],
                         "width": best.get("width"), "height": best.get("height"),
                         "source_status": "direct_public_snapshot_json" if any("json_path" in e for e in best["evidence"]) else "direct_public_dom_image",
                         "evidence": best["evidence"], "owner_ids": photo["owner_ids"],
                         "season_ids": [], "program_ids": [], "rights_status": "unknown", "privacy_review_required": True,
                         "selection_note": "Largest declared native dimensions among delivered variants; DOM dimensions are not treated as native image dimensions."})
    result["counts"]["photos_with_metadata_or_id"] = len(result["photos"])
    result["counts"]["photos_with_image_urls"] = len(manifest)
    result["counts"]["dom_discoveries_with_video_urls"] = sum(bool(p["video_urls"]) for p in result["dom_post_discoveries"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.media_manifest:
        args.media_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.media_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
