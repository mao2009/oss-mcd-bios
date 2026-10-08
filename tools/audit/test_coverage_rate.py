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
        self.assertTrue(cr.defined(row(blocker="Y (OQ-7)")))  # Y items keep their blocker

    def test_rates_are_cumulative(self):
        rows = [row(level="LA"), row(level="LB", impl="N", id="T-02"), row(level="LC", prov="P-OFF", id="T-03")]
        by = cr.rates(rows)["All areas"]
        self.assertEqual(by["LA"], (1, 1, 1, 1))
        self.assertEqual(by["LB"], (1, 1, 1, 2))
        self.assertEqual(by["LC"], (2, 1, 2, 3))

    def test_provenance_references_expand(self):
        a, b = row(prov="P-RE"), row(prov="as above", id="T-02")
        self.assertIn("P-RE", cr.provenance([a, b])["T-02"])

    def test_table_rows_rejects_short_row(self):
        text = "| A | B |\n| --- | --- |\n| T-01 | x |\n\n" + cr.HEADER + "\n| " + " | ".join(["---"] * 12) + " |\n| T-02 | x |\n"
        with self.assertRaises(ValueError):
            cr.table_rows(text)


class Matrix(unittest.TestCase):
    def test_matrix_matches_area_files(self):
        rows = cr.area_rows()
        self.assertEqual(len(rows), 406)
        text = cr.MATRIX.read_text(encoding="utf-8")
        self.assertEqual(cr.regenerate(text, rows), text)
        self.assertEqual([cr.item_id(r) for r in cr.table_rows(text)], [cr.item_id(r) for r in rows])


if __name__ == "__main__":
    unittest.main()
