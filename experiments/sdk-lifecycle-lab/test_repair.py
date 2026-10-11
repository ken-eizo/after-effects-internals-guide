"""Tests for the exact ownership transformation; run repair.py first."""
from pathlib import Path
import unittest
import repair


class OwnershipRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (repair.HERE / "workbench/original/SmartyPants.cpp").read_bytes()

    def test_round_trip_and_no_changes_outside_actually_render(self):
        fixed = repair.repair_smarty(self.original)
        self.assertEqual(repair.repair_smarty(fixed, reverse=True), self.original)
        before = self.original.decode()
        after = fixed.decode()
        a, b = repair.function_span(before, "ActuallyRender")
        c, d = repair.function_span(after, "ActuallyRender")
        self.assertEqual(before[:a], after[:c])
        self.assertEqual(before[b:], after[d:])
        body = after[c:d]
        self.assertNotIn("in_data->sequence_data", body)
        self.assertIn("SmartyPantsData\t\trender_data{}", body)
        self.assertIn("id->channel = channel_paramP->u.pd.value", body)

    def test_unknown_and_duplicate_preimages_are_rejected(self):
        for data in (b"not SDK source", self.original + self.original,
                     self.original.replace(b"SmartyPantsData\t\t*id;",
                                           b"SmartyPantsData\t\t*changed;")):
            with self.assertRaises(ValueError):
                repair.repair_smarty(data)

    def test_already_fixed_requires_explicit_reverse(self):
        fixed = repair.repair_smarty(self.original)
        with self.assertRaises(ValueError):
            repair.repair_smarty(fixed)

    def test_independent_function_edits_compose(self):
        # A separate Alpha16 correction is preserved while patching ownership.
        before = b"(PF_MAX_CHAN8 - id->blend) * (PF_MAX_CHAN16 - in->alpha)"
        after = b"(256 - id->blend) * (PF_MAX_CHAN16 - in->alpha)"
        self.assertEqual(self.original.count(before), 1)
        composed = self.original.replace(before, after)
        fixed = repair.repair_smarty(composed)
        self.assertIn(after, fixed)
        self.assertEqual(repair.repair_smarty(fixed, reverse=True), composed)

    def test_destination_escape_is_rejected(self):
        with self.assertRaises(ValueError):
            repair.local_path(repair.HERE.parent / "outside.cpp")


if __name__ == "__main__":
    unittest.main(verbosity=2)
