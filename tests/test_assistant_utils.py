import os
import tempfile
import time
import unittest

from assistant_utils import (
    contains_any,
    get_latest_supported_file,
    is_supported_file,
    select_best_ocr_match,
)


class AssistantUtilsTests(unittest.TestCase):
    def test_supported_extensions_are_case_insensitive(self):
        self.assertTrue(is_supported_file("notes.TXT"))
        self.assertTrue(is_supported_file("resume.PDF"))
        self.assertTrue(is_supported_file("letter.docx"))
        self.assertFalse(is_supported_file("photo.png"))

    def test_latest_supported_file_ignores_other_files(self):
        with tempfile.TemporaryDirectory() as directory:
            older = os.path.join(directory, "older.txt")
            newer = os.path.join(directory, "newer.pdf")
            ignored = os.path.join(directory, "newest.png")
            for path in (older, newer, ignored):
                open(path, "w", encoding="utf-8").close()
            now = time.time()
            os.utime(older, (now - 30, now - 30))
            os.utime(newer, (now - 20, now - 20))
            os.utime(ignored, (now, now))
            self.assertEqual(get_latest_supported_file(directory), newer)

    def test_missing_or_empty_directory_returns_none(self):
        self.assertIsNone(get_latest_supported_file("/directory/that/does/not/exist"))
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(get_latest_supported_file(directory))

    def test_contains_any_normalizes_commands(self):
        self.assertTrue(contains_any("  OPEN YouTube  ", ["open youtube"]))
        self.assertFalse(contains_any("open google", ["open youtube"]))

    def test_select_best_ocr_match(self):
        results = [
            ("box-one", "Python tutorial", 0.91),
            ("box-two", "Music playlist", 0.99),
        ]

        def scorer(target, detected):
            return 95 if "python" in detected else 10

        self.assertEqual(
            select_best_ocr_match("python course", results, scorer),
            ("box-one", "Python tutorial", 95),
        )

    def test_empty_ocr_target_has_no_match(self):
        self.assertIsNone(select_best_ocr_match("", [], lambda _a, _b: 100))


if __name__ == "__main__":
    unittest.main()
