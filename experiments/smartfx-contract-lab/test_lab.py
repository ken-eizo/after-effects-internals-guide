"""Local patch-scope regressions; run lab.py once to prepare the source copies."""
import unittest
from pathlib import Path
import lab


class PreRenderPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(lab.WORK / "original" / "SmartyPants.cpp").read_text()

    def test_only_prerender_changes(self):
        before=lab.function(self.source,"PreRender")
        fixed=lab.repair(self.source)
        after=lab.function(fixed,"PreRender")
        self.assertEqual(self.source.replace(before,"FUNCTION"), fixed.replace(after,"FUNCTION"))

    def test_other_owned_edits_survive_composition(self):
        changed=self.source.replace("out->alpha = 1.0 - in->alpha;",
                                    "out->alpha = in->alpha; // independent overlay")
        fixed=lab.repair(changed)
        self.assertIn("out->alpha = in->alpha; // independent overlay",fixed)
        self.assertEqual(lab.function(fixed,"PreRender"),
                         lab.function(lab.repair(self.source),"PreRender"))

    def test_second_application_refused(self):
        with self.assertRaisesRegex(ValueError,"patch preimage"):
            lab.repair(lab.repair(self.source))

    def test_changed_preimage_refused(self):
        changed=self.source.replace("PF_CheckoutResult in_result;",
                                    "PF_CheckoutResult changed_name;")
        with self.assertRaisesRegex(ValueError,"patch preimage"):
            lab.repair(changed)

    def test_harness_extracts_combined_source(self):
        fixed=lab.repair(self.source)
        harness=lab.harness_for_source(fixed)
        self.assertIn(lab.function(fixed,"PreRender"),harness)
        self.assertNotIn("// EXTRACTED_PRERENDER",harness)
        self.assertIn('#include "AE_Macros.h"',harness)


if __name__=="__main__":
    unittest.main(verbosity=2)
