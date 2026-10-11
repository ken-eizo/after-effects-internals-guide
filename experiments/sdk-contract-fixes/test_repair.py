"""Regression tests for reversible local-copy edits. Run prepare first."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import repair


class RepairSafetyTests(unittest.TestCase):
    def setUp(self):
        self.sources = {name: (repair.WORK / "original" / name).read_bytes() for name in repair.PATCHES}
        self.provenance = (repair.WORK / "provenance.json").read_bytes()
        self.temp = tempfile.TemporaryDirectory(dir=repair.WORK)
        self.work = Path(self.temp.name)
        for group in ["original", "copy"]:
            (self.work / group).mkdir()
            for name, data in self.sources.items():
                (self.work / group / name).write_bytes(data)
        (self.work / "provenance.json").write_bytes(self.provenance)
        self.mock = patch.object(repair, "WORK", self.work)
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.temp.cleanup()

    def test_actual_source_round_trip_and_idempotence(self):
        self.assertEqual(repair.apply()["changed_files"], 2)
        self.assertEqual(repair.apply()["changed_files"], 0)
        for name, data in self.sources.items():
            fixed = (self.work / "copy" / name).read_bytes()
            self.assertEqual(repair.change(fixed, name, reverse=True), data)
        self.assertEqual(repair.apply(reverse=True)["changed_files"], 2)
        self.assertEqual(repair.apply(reverse=True)["changed_files"], 0)
        for name, data in self.sources.items():
            self.assertEqual((self.work / "copy" / name).read_bytes(), data)
            self.assertEqual((self.work / "original" / name).read_bytes(), data)

    def test_changed_working_copy_refused_before_any_write(self):
        target = self.work / "copy" / "compute-cache-key.cpp"
        target.write_bytes(target.read_bytes() + b"\n// operator edit\n")
        with self.assertRaisesRegex(ValueError, "unrecognized edits"):
            repair.apply()
        self.assertEqual((self.work / "copy" / "SmartyPants.cpp").read_bytes(), self.sources["SmartyPants.cpp"])
        self.assertTrue(target.read_bytes().endswith(b"// operator edit\n"))

    def test_changed_original_refused(self):
        target = self.work / "original" / "SmartyPants.cpp"
        target.write_bytes(target.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "original copy changed"):
            repair.apply()

    def test_ambiguous_patch_refused(self):
        for name, data in self.sources.items():
            with self.assertRaisesRegex(ValueError, "exactly one"):
                repair.change(data + data, name)

    def test_missing_patch_refused(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            repair.change(b"unrelated source", "SmartyPants.cpp")

    def test_outside_package_destination_refused(self):
        with self.assertRaisesRegex(ValueError, "escapes package"):
            repair.local_path(repair.HERE.parent / "not-owned.cpp")

    def test_alpha_branch_and_blend_dispatch_are_from_real_source(self):
        text = self.sources["SmartyPants.cpp"].decode()
        render = repair.function(text, "ActuallyRender")
        self.assertIn("id->blend = (A_short)(2.56 * blend_paramP->u.fs_d.value);", render)
        self.assertIn("if (id->blend == 256)", render)
        self.assertIn("PF_COPY(input, output, &src_rect, NULL)", render)
        for suffix in ["8", "16", "Float"]:
            function = repair.function(text, "InvertPixel" + suffix)
            self.assertIn("case Channel_ALPHA:", function)


if __name__ == "__main__":
    unittest.main(verbosity=2)
