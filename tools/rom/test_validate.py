"""Unit tests for validate.py. Run: python3 -I -B -m unittest discover -s tools/rom -p "test_*.py" -v

testdata/invariants-issue1.json is a verbatim copy of docs/specifications/invariants.json from
branch agent-a/issue-1-rom-layout (commit c2abc36, schema_version 2), used as a fixture.
"""
import contextlib
import copy
import io
import json
import os
import tempfile
import unittest

import validate

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "testdata", "invariants-issue1.json")
SIZE = 131072
CONFIG = {"rom_size": SIZE, "fill_byte": 255}
ENFORCED = {"INV-001", "INV-002", "INV-003", "INV-004", "INV-005"}


def make_rom(patches=None):
    """Synthetic image shaped like the build output; patches = {offset: bytes}."""
    rom = bytearray(b"\xff" * SIZE)
    rom[0:8] = bytes.fromhex("00FFFE00 00000100")
    for off in range(8, 256, 4):
        rom[off:off + 4] = (0x10A).to_bytes(4, "big")
    for off, data in (patches or {}).items():
        rom[off:off + len(data)] = data
    return bytes(rom)


def fixture_doc():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def results(rom, invariants):
    return {iid: r for r, iid, _ in validate.run_checks(rom, invariants)}


def inv(check_type, status="PROJECT-RULE", scope="project", enforceable=True, **params):
    return {"id": "INV-900", "description": "test", "status": status, "enforceable": enforceable,
            "scope": scope, "source": [], "check": dict(type=check_type, **params)}


class Issue1Fixture(unittest.TestCase):
    def test_fixture_is_schema_valid(self):
        self.assertEqual(validate.schema_errors(fixture_doc()), [])

    def test_good_rom_passes_enforced_and_skips_rest(self):
        r = results(make_rom(), fixture_doc()["invariants"])
        self.assertEqual({k for k, v in r.items() if v == "PASS"}, ENFORCED)
        self.assertEqual({k for k, v in r.items() if v == "SKIP"}, set(r) - ENFORCED)

    def test_each_enforced_invariant_can_fail(self):
        cases = {
            "INV-001": make_rom()[:-2],
            "INV-002": make_rom({4: bytes.fromhex("00000101")}),
            "INV-003": make_rom({4: bytes.fromhex("00020000")}),
            "INV-004": make_rom({0: bytes.fromhex("00FFFE01")}),
            "INV-005": make_rom({252: bytes.fromhex("00000101")}),
        }
        for iid, rom in cases.items():
            with self.subTest(iid):
                self.assertEqual(results(rom, fixture_doc()["invariants"])[iid], "FAIL")

    def test_advisory_mismatch_is_skip(self):
        r = results(make_rom({0x120: b"CDX BOOT ROM    "}), fixture_doc()["invariants"])
        self.assertEqual(r["INV-006"], "SKIP")

    def test_mask_and_exclude(self):
        r = results(make_rom({4: bytes.fromhex("FF000100"), 112: bytes.fromhex("00FF0001")}), fixture_doc()["invariants"])
        self.assertEqual((r["INV-003"], r["INV-005"]), ("PASS", "PASS"))


class Schema(unittest.TestCase):
    def doc(self, *invs):
        return {"schema_version": 2, "invariants": list(invs)}

    def assertMalformed(self, doc):
        self.assertTrue(validate.schema_errors(doc), doc)

    def test_valid_minimal(self):
        self.assertEqual(validate.schema_errors(self.doc(inv("size_equals", bytes=1))), [])

    def test_version(self):
        for v in (1, 3, None):
            self.assertMalformed({"schema_version": v, "invariants": []})

    def test_enforceability_rule(self):
        self.assertMalformed(self.doc(inv("size_equals", status="ESTIMATED", scope="hardware", bytes=1)))
        self.assertMalformed(self.doc(inv("size_equals", status="CONFIRMED", scope="emulator:gpgx", bytes=1)))
        ok = self.doc(inv("size_equals", status="CONFIRMED", scope="hardware", bytes=1),
                      dict(inv("size_equals", status="ESTIMATED", scope="emulator:gpgx", enforceable=False, bytes=1),
                           id="INV-901"))
        self.assertEqual(validate.schema_errors(ok), [])

    def test_unknown_type_rejected_even_if_advisory(self):
        self.assertMalformed(self.doc(inv("magic")))
        self.assertMalformed(self.doc(inv("magic", status="ESTIMATED", enforceable=False)))

    def test_field_errors(self):
        good = inv("size_equals", bytes=1)
        for broken in (dict(good, id="X-1"), dict(good, status="MAYBE"), dict(good, scope="emulator:GPGX"),
                       dict(good, enforceable="yes"), {k: v for k, v in good.items() if k != "source"},
                       inv("size_equals"), inv("bytes_not_in", offset=0, length=4, ascii_values=["ABC"])):
            with self.subTest(broken):
                self.assertMalformed(self.doc(broken))
        self.assertMalformed(self.doc(good, good))  # duplicate id


class Checks(unittest.TestCase):
    def test_check_types(self):
        rom = make_rom({0x100: b"SEGA", 0x128: b"BOOT"})
        cases = [
            (inv("u32_in_ranges", offset=0, mask=0xFFFFFF, ranges=[[0, 0], [0xFF0000, 0xFFFFFF]]), "PASS"),
            (inv("u32_in_ranges", offset=4, ranges=[[0, 0]]), "FAIL"),
            (inv("u32_each_in_ranges", start=8, end=252, step=4, ranges=[[0, 0x1FFFF]]), "PASS"),
            (inv("u16_in", offset=0, values=[255]), "PASS"),
            (inv("u16_in", offset=0, values=[0xFF00]), "FAIL"),  # little-endian reading would pass
            (inv("bytes_equal", offset=0x100, ascii="SEGA"), "PASS"),
            (inv("bytes_equal_any", offsets=[0x124, 0x128], ascii="BOOT"), "PASS"),
            (inv("bytes_equal_any", offsets=[0x124], ascii="BOOT"), "FAIL"),
            (inv("bytes_not_in", offset=0x100, length=4, ascii_values=["SEGA"]), "FAIL"),
        ]
        for i, want in cases:
            with self.subTest(i["check"]):
                self.assertEqual(results(rom, [i])["INV-900"], want)

    def test_read_past_end_fails(self):
        for i in (inv("u32_even", offset=SIZE - 2), inv("bytes_equal", offset=SIZE - 1, ascii="AB"),
                  inv("u32_even_each", start=SIZE - 4, end=SIZE, step=4)):
            self.assertEqual(results(make_rom(), [i])["INV-900"], "FAIL")

    def test_builtins(self):
        self.assertEqual(set(results(make_rom(), validate.builtin_invariants(CONFIG)).values()), {"PASS"})
        self.assertIn("FAIL", results(make_rom()[:100], validate.builtin_invariants(CONFIG)).values())


class Main(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.cfg = self.write("c.json", json.dumps(CONFIG))
        self.rom = self.write("r.bin", make_rom())

    def write(self, name, data):
        path = os.path.join(self.dir, name)
        with open(path, "wb" if isinstance(data, bytes) else "w") as f:
            f.write(data)
        return path

    def run_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = validate.main(list(args) + ["--config", self.cfg])
        return code, out.getvalue()

    def test_fixture_file_end_to_end(self):
        code, out = self.run_main(self.rom, "--invariants", FIXTURE)
        self.assertEqual(code, 0, out)
        self.assertIn("0 failed, 7 skipped", out)
        code, out = self.run_main(self.write("bad.bin", make_rom({4: b"\0\0\1\1"})), "--invariants", FIXTURE)
        self.assertEqual(code, 1, out)

    def test_malformed_file_rejected(self):
        doc = fixture_doc()
        doc["invariants"][5]["enforceable"] = True  # INV-006 is emulator-scoped
        code, out = self.run_main(self.rom, "--invariants", self.write("i.json", json.dumps(doc)))
        self.assertEqual(code, 1, out)
        self.assertIn("malformed", out)
        code, out = self.run_main(self.rom, "--invariants", self.write("j.json", "{not json"))
        self.assertEqual(code, 1, out)

    def test_without_invariants_file(self):
        code, out = self.run_main(self.rom, "--invariants", os.path.join(self.dir, "none.json"))
        self.assertEqual(code, 0, out)
        self.assertIn("built-in checks only", out)

    def test_missing_rom_fails(self):
        self.assertEqual(self.run_main(os.path.join(self.dir, "nope.bin"))[0], 1)


if __name__ == "__main__":
    unittest.main()
