"""Unit tests for validate.py. Run: python3 -I -B -m unittest discover -s tools/rom -p "test_*.py" -v"""
import contextlib
import io
import json
import os
import tempfile
import unittest

import validate

ROM = bytes.fromhex("00FFFE00" "00000100" "0000") + b"\xff" * 10  # 20 bytes
CONFIG = {"rom_size": 20, "fill_byte": 255}


def c(kind, status="CONFIRMED", **params):
    return dict(id=kind, kind=kind, status=status, **params)


class RunChecks(unittest.TestCase):
    def result(self, check, rom=ROM):
        return validate.run_checks(rom, [check])[0][0]

    def test_builtins_pass_on_good_rom(self):
        self.assertEqual({r for r, _, _ in validate.run_checks(ROM, validate.builtin_checks(CONFIG))}, {"PASS"})

    def test_size(self):
        self.assertEqual(self.result(c("size_equals", size=20)), "PASS")
        self.assertEqual(self.result(c("size_equals", size="0x20")), "FAIL")
        self.assertEqual(self.result(c("min_size", size=21)), "FAIL")

    def test_big_endian_reads(self):
        self.assertEqual(self.result(c("u32_be_equals", offset=0, value="0x00FFFE00")), "PASS")
        self.assertEqual(self.result(c("u32_be_equals", offset=0, value="0x00FEFF00")), "FAIL")  # little-endian would match this
        self.assertEqual(self.result(c("u16_be_equals", offset=6, value="0x0100")), "PASS")
        self.assertEqual(self.result(c("bytes_equal", offset=8, hex="0000ff")), "PASS")

    def test_odd_vector_fails(self):
        rom = ROM[:7] + b"\x01" + ROM[8:]
        self.assertEqual(self.result(c("u32_be_even", offset=4), rom), "FAIL")

    def test_out_of_range_fails_not_crashes(self):
        self.assertEqual(self.result(c("u32_be_even", offset=18)), "FAIL")
        self.assertEqual(self.result(c("u32_be_even", offset=-1)), "FAIL")

    def test_only_confirmed_enforced(self):
        self.assertEqual(self.result(c("size_equals", status="UNVERIFIED", size=1)), "SKIP")
        self.assertEqual(self.result({"id": "x", "kind": "size_equals", "size": 1}), "SKIP")

    def test_unknown_kind_or_missing_param_fails_closed(self):
        self.assertEqual(self.result(c("checksum_magic")), "FAIL")
        self.assertEqual(self.result(c("size_equals")), "FAIL")


class Main(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, data):
        path = os.path.join(self.tmp.name, name)
        with open(path, "wb" if isinstance(data, bytes) else "w") as f:
            f.write(data)
        return path

    def run_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = validate.main(list(args))
        return code, out.getvalue()

    def test_without_invariants_file(self):
        rom, cfg = self.write("r.bin", ROM), self.write("c.json", json.dumps(CONFIG))
        code, out = self.run_main(rom, "--config", cfg, "--invariants", os.path.join(self.tmp.name, "missing.json"))
        self.assertEqual(code, 0, out)
        self.assertIn("built-in checks only", out)

    def test_missing_rom_fails(self):
        cfg = self.write("c.json", json.dumps(CONFIG))
        code, _ = self.run_main(os.path.join(self.tmp.name, "nope.bin"), "--config", cfg)
        self.assertEqual(code, 1)

    def test_invariants_file_object_and_list_forms(self):
        rom, cfg = self.write("r.bin", ROM), self.write("c.json", json.dumps(CONFIG))
        bad = c("u16_be_equals", offset=0, value=1)
        for doc in ({"invariants": [bad]}, [bad]):
            inv = self.write("i.json", json.dumps(doc))
            code, out = self.run_main(rom, "--config", cfg, "--invariants", inv)
            self.assertEqual(code, 1, out)
        inv = self.write("i.json", json.dumps([dict(bad, status="UNVERIFIED")]))
        self.assertEqual(self.run_main(rom, "--config", cfg, "--invariants", inv)[0], 0)


if __name__ == "__main__":
    unittest.main()
