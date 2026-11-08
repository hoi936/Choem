"""Offline tests: synthetic URLs and image bytes, never real network requests."""
from email.message import Message
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

COLLECTION = Path(__file__).resolve().parents[1] / "collection"
sys.path.insert(0, str(COLLECTION))
import archive
import download_public_media as downloader


class PublicDownloaderTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cho-em-download-fixture-")
        self.root = Path(self.temporary.name)
        archive.initialize(self.root)
        (self.root / "snapshot.html").write_text("SYNTHETIC FIXTURE", encoding="utf-8")
        self.manifest = self.root / "fixture-manifest.json"
        self.item = {"source_url": "https://scontent.fixture.fbcdn.net/test.jpg?sig=KEEP",
                     "provenance_snapshot": "snapshot.html", "rights_status": "unknown",
                     "source_post_url": "https://www.facebook.com/456/posts/123",
                     "description": "SYNTHETIC TEST IMAGE"}
        self.manifest.write_text(json.dumps([self.item]), encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_dry_run_never_constructs_network_opener(self):
        with patch.object(downloader, "build_opener") as opener:
            result = downloader.download_manifest(self.root, self.manifest, dry_run=True)
        opener.assert_not_called()
        self.assertEqual(0, result["network_requests"])
        self.assertEqual(1, result["validated_images"])

    def test_rejects_non_cdn_and_missing_snapshot(self):
        for url in ("http://fbcdn.net/a.jpg", "https://fbcdn.net.attacker.invalid/a.jpg",
                    "https://user:secret@fbcdn.net/a.jpg", "https://facebook.com/a.jpg"):
            with self.assertRaises(ValueError):
                downloader.validate_url(url)
        (self.root / "snapshot.html").unlink()
        with self.assertRaises(ValueError):
            downloader.manifest_records(self.root, self.manifest)

    def test_http403_stops_manifest_without_retry(self):
        try:
            import PIL
        except ImportError:
            self.skipTest("Pillow is not installed")
        self.manifest.write_text(json.dumps([self.item, self.item]), encoding="utf-8")
        with patch.object(downloader, "build_opener") as make_opener:
            make_opener.return_value.open.side_effect = HTTPError(
                self.item["source_url"], 403, "Forbidden", {}, io.BytesIO(b"denied"))
            result = downloader.download_manifest(self.root, self.manifest)
            self.assertEqual(1, make_opener.return_value.open.call_count)
        self.assertTrue(result["stopped"])
        attempts = archive.read_json(self.root / "research/download_attempts.json")
        self.assertEqual("access_stopped", attempts[0]["status"])
        self.assertEqual([], archive.read_json(self.root / "data/raw/photos.json"))

    def test_original_bytes_and_evidence_preserved_cached_rerun_no_network(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")
        buffer = io.BytesIO()
        Image.new("RGB", (4, 3), "blue").save(buffer, format="PNG")
        original = buffer.getvalue()
        response = io.BytesIO(original)
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "image/png"
        response.headers["Content-Length"] = str(len(original))
        response.geturl = lambda: self.item["source_url"]
        with patch.object(downloader, "build_opener") as make_opener:
            make_opener.return_value.open.return_value = response
            result = downloader.download_manifest(self.root, self.manifest)
            self.assertEqual(1, make_opener.return_value.open.call_count)
        self.assertEqual(1, result["downloaded"])
        photo = archive.read_json(self.root / "data/raw/photos.json")[0]
        self.assertEqual(original, (self.root / photo["local_path"]).read_bytes())
        self.assertEqual("unknown", photo["rights_status"])
        self.assertTrue(photo["privacy_review_required"])
        self.assertEqual(self.item["source_post_url"], photo["source_post_url"])
        self.assertEqual("downloaded", photo["download_status"])
        self.assertEqual("snapshot.html", photo["retrievals"][0]["provenance_snapshot"])
        with patch.object(downloader, "build_opener") as make_opener:
            result = downloader.download_manifest(self.root, self.manifest)
            make_opener.return_value.open.assert_not_called()
        self.assertEqual(1, result["skipped_existing"])
        self.assertEqual(1, len(archive.read_json(self.root / "data/raw/photos.json")))


if __name__ == "__main__":
    unittest.main()
