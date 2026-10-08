import unittest

from tools.audit import coverage_rate as cr


def row(impl="Y", material="Y", own_test="Y", blocker="N", level="LA", ref="x", prov="MIT", id="T-01"):
    return [id, "b", level, material, ref, prov, impl, "-", own_test, "Y", "N", blocker]


class Classify(unittest.TestCase):
    def test_head(self):
        self.assertEqual(cr.head("**Cond** (x)"), "Cond")
        self.assertEqual(cr.head("Y: five sources"), "Y")
        self.assertEqual(cr.head("**N under current policy**"), "N")
        self.assertEqual(cr.head("partial (ESTIMATED)"), "Partial")
        self.assertEqual(cr.head("n/a"), "")

    def test_level_counts_lb_lc_at_lb(self):
        self.assertEqual(cr.level(row(level="LB/LC")), "LB")

    def test_defined_rules(self):
        self.assertTrue(cr.defined(row()))
        self.assertFalse(cr.defined(row(impl="N")))
        self.assertFalse(cr.defined(row(impl="Cond: emulators **conflict**")))
        self.assertFalse(cr.defined(row(material="partial (UNCONFIRMED)")))
        self.assertFalse(cr.defined(row(impl="Cond", own_test="N")))
        self.assertFalse(cr.defined(row(material="partial", own_test="Partial")))
        self.assertTrue(cr.defined(row(impl="Cond", material="partial")))
        self.assertFalse(cr.defined(row(impl="Cond", blocker="**Y (LC)**")))
        self.assertFalse(cr.defined(row(impl="Cond", blocker="via API-60")))  # inherited blocker
        self.assertTrue(cr.defined(row(blocker="Y (OQ-7)")))  # Y items keep their blocker

    def test_provenance_taint_and_override(self):
        rows = [row(prov="P-UNK, 0BSD"), row(prov="as above", id="T-02"),
                row(prov="MEGADEV quotes official text", id="T-03"),
                row(prov="emulator + CPU official", id="T-04"),
                row(impl="Cond (placement CONFIRMED only via an excluded doc)", id="T-05")]
        cls = cr.classify(rows, {})
        self.assertEqual([cls[i]["clean"] for i in ("T-01", "T-02", "T-03", "T-04", "T-05")],
                         [False, False, False, True, False])
        self.assertTrue(cr.classify(rows, {}, {"T-01"})["T-01"]["clean"])

    def test_dispute_demotes_whole_group(self):
        rows = [row(), row(id="T-02", impl="N"), row(id="T-03")]
        cls = cr.classify(rows, {"X-01": ["T-01", "T-02"]})
        self.assertFalse(cls["T-01"]["undisputed"])
        self.assertTrue(cls["T-03"]["undisputed"])

    def test_rates_are_cumulative(self):
        rows = [row(level="LA"), row(level="LB", impl="N", id="T-02"), row(level="LC", prov="P-OFF", id="T-03")]
        by = cr.rates(rows, {})
        head, lenient = by[cr.VIEWS[0][0]]["All areas"], by[cr.VIEWS[3][0]]["All areas"]
        self.assertEqual((head["LA"], head["LB"], head["LC"]), ((1, 1), (1, 2), (1, 3)))
        self.assertEqual(lenient["LC"], (2, 3))

    def test_groups_and_overrides_parse(self):
        text = "| X-01 | t | ROM-65, COM-52 | x |\n   | H-01 | ROM-28 | why |\n"
        self.assertEqual(cr.groups(text), {"X-01": ["ROM-65", "COM-52"]})
        self.assertEqual(cr.overrides(text), {"ROM-28"})

    def test_table_rows_rejects_short_row(self):
        text = "| A | B |\n| --- | --- |\n| T-01 | x |\n\n" + cr.HEADER + "\n| " + " | ".join(["---"] * 12) + " |\n| T-02 | x |\n"
        with self.assertRaises(ValueError):
            cr.table_rows(text)


class Matrix(unittest.TestCase):
    def test_matrix_matches_area_files(self):
        text = cr.MATRIX.read_text(encoding="utf-8")
        g = cr.groups(text)
        self.assertEqual(len(g), 22)
        self.assertEqual(len(cr.overrides(text)), 5)
        rows = cr.area_rows(g)
        self.assertEqual(len(rows), 406)
        self.assertEqual(cr.regenerate(text, rows, g), text)


if __name__ == "__main__":
    unittest.main()