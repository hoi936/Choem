"""Tests use only isolated temporary archives and fabricated fixtures."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "collection/archive.py"
SPEC = importlib.util.spec_from_file_location("archive", MODULE)
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cho-em-fixture-")
        self.root = Path(self.temporary.name)
        archive.initialize(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def write_export(self, value):
        path = self.root / "synthetic-test-export.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_init_preserves_existing_verified_records(self):
        path = self.root / "data/processed/seasons.json"
        original = [{"season_id": "fixture", "verification_status": "verified"}]
        archive.atomic_json(path, original)
        archive.initialize(self.root)
        self.assertEqual(original, archive.read_json(path))
        self.assertEqual([], archive.read_json(self.root / "data/raw/posts.json"))
        self.assertFalse((self.root / "data/seasons/season_01").exists())

    def test_discovery_canonicalization_and_idempotency(self):
        first = "https://m.facebook.com/story.php?story_fbid=123&id=456&tracking=yes"
        second = "https://www.facebook.com/456/posts/123/?fbclid=test"
        archive.discover(self.root, [first, second])
        self.assertEqual(1, len(archive.read_json(self.root / "data/raw/discovered_urls.json")))
        archive.discover(self.root, [first])
        self.assertEqual(1, archive.status(self.root)["pipeline_counts"]["discovered"])

    def test_import_preserves_exact_caption_and_is_idempotent(self):
        caption = "TƯ LIỆU THỬ — CHO EM ♥️\n\nXin chào!  #ThửNghiệm\n"
        entry = {"timestamp": 1712000000, "post_url": "https://www.facebook.com/456/posts/123",
                 "data": [{"post": caption}]}
        source = self.write_export({"your_posts_v2": [entry]})
        archive.import_export(self.root, source)
        result = archive.import_export(self.root, source)
        posts = archive.read_json(self.root / "data/raw/posts.json")
        self.assertEqual(0, result["inserted"])
        self.assertEqual(1, len(posts))
        self.assertEqual(caption, posts[0]["caption_original"])
        self.assertEqual("complete", posts[0]["caption_completeness"])
        self.assertEqual(source.read_bytes(), (self.root / posts[0]["provenance"]["source_file"]).read_bytes())
        source = self.write_export({"your_posts_v2": [{**entry, "data": [{"post": "CHANGED FIXTURE"}]}]})
        archive.import_export(self.root, source)
        self.assertEqual(caption, archive.read_json(self.root / "data/raw/posts.json")[0]["caption_original"])
        self.assertEqual(1, len(archive.read_json(self.root / "research/import_conflicts.json")))

    def test_unknown_shape_does_not_claim_complete_caption(self):
        source = self.write_export([{"id": "fixture", "message": "sample excerpt…"}])
        archive.import_export(self.root, source)
        self.assertEqual("unknown", archive.read_json(self.root / "data/raw/posts.json")[0]["caption_completeness"])

    def test_unknown_season_rejected_before_post_index_is_changed(self):
        source = self.write_export([{"caption_original": "test", "season_ids": ["fictional-season"]}])
        with self.assertRaises(ValueError):
            archive.import_export(self.root, source)
        self.assertEqual([], archive.read_json(self.root / "data/raw/posts.json"))

    def test_media_deduplicates_original_preserves_all_post_references(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")
        source = self.write_export([{"post_url": f"https://www.facebook.com/456/posts/{number}",
                                     "caption_original": "TEST FIXTURE"} for number in (123, 124)])
        archive.import_export(self.root, source)
        posts = archive.read_json(self.root / "data/raw/posts.json")
        photo = self.root / "fixture.png"
        Image.new("RGB", (3, 2), "red").save(photo)
        original = photo.read_bytes()
        first = archive.import_media(self.root, photo, post_id=posts[0]["post_id"])
        second = archive.import_media(self.root, photo, post_id=posts[1]["post_id"])
        self.assertTrue(second["deduplicated"])
        self.assertEqual(first["photo_id"], second["photo_id"])
        self.assertEqual(original, (self.root / first["local_path"]).read_bytes())
        photos = archive.read_json(self.root / "data/raw/photos.json")
        self.assertEqual(1, len(photos))
        self.assertEqual(2, len(photos[0]["post_ids"]))
        self.assertTrue(photos[0]["privacy_review_required"])
        self.assertEqual("unknown", photos[0]["rights_status"])
        self.assertEqual(None, photos[0]["downloaded_at"])
        self.assertEqual((3, 2), (photos[0]["width"], photos[0]["height"]))


if __name__ == "__main__":
    unittest.main()
