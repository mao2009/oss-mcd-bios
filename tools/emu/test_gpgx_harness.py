"""Unit tests for gpgx_harness.py. The emulator process boundary (run_host/git_head) is mocked.

  python -I tools/emu/test_gpgx_harness.py
The final test runs the real pinned core only if `gpgx_harness.py fetch` has been run; else it skips.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpgx_harness as h  # noqa: E402

PIN = "a" * 40
LOCK = {"repo": "https://example.invalid/gpgx", "commit": PIN}


def host_ok(main_ram=b"OKOK", regions=("68KRAM", "PRGRAM"), loaded=True, rc=0, stdout=None):
    """Fake child host: writes main.bin into the workdir it was given (cmd[6])."""
    def fake(cmd, timeout):
        with open(os.path.join(cmd[6], "main.bin"), "wb") as fh:
            fh.write(main_ram.ljust(0x10000, b"\0"))
        out = stdout if stdout is not None else json.dumps(
            {"loaded": loaded, "regions": list(regions), "frames_run": int(cmd[5]), "samples": [], "core_log": []})
        return subprocess.CompletedProcess(cmd, rc, out, "")
    return fake


class Harness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rom = os.path.join(self.tmp.name, "rom.bin")
        with open(self.rom, "wb") as fh:
            fh.write(h.make_fixture())
        self.gpgx = os.path.join(self.tmp.name, "gpgx")
        os.makedirs(self.gpgx)
        open(h.core_path(self.gpgx), "wb").close()
        p = mock.patch.object(h, "git_head", return_value=PIN)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def run_h(self, fake=None, expects=("main:FF0000=4F4B4F4B",), rom=None):
        with mock.patch.object(h, "run_host", side_effect=fake or host_ok()) as rh:
            res = h.run(rom or self.rom, self.gpgx, 10, list(expects), lock=LOCK)
        self.assertLessEqual({"status", "rom_sha256", "emulator_sha", "command", "trace", "reason"}, set(res))
        self.assertTrue(res["reason"])
        return res, rh

    def test_pass_when_checkpoint_holds(self):
        res, _ = self.run_h()
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["emulator_sha"], PIN)
        self.assertEqual(len(res["rom_sha256"]), 64)
        self.assertIn("-I", res["command"])

    def test_fail_when_checkpoint_differs(self):
        self.assertEqual(self.run_h(host_ok(main_ram=b"NOPE"))[0]["status"], "FAIL")

    def test_blocked_without_expectations_never_pass(self):
        res, rh = self.run_h(expects=())
        self.assertEqual(res["status"], "BLOCKED")
        rh.assert_called_once()

    def test_missing_rom_blocked(self):
        res, rh = self.run_h(rom=os.path.join(self.tmp.name, "nope.bin"))
        self.assertEqual(res["status"], "BLOCKED")
        rh.assert_not_called()

    def test_rom_without_br_header_blocked(self):
        with open(self.rom, "r+b") as fh:
            fh.seek(0x180)
            fh.write(b"GM")
        res, rh = self.run_h()
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("'BR'", res["reason"])
        rh.assert_not_called()

    def test_missing_core_skip(self):
        os.remove(h.core_path(self.gpgx))
        res, rh = self.run_h()
        self.assertEqual(res["status"], "SKIP")
        rh.assert_not_called()

    def test_wrong_revision_blocked(self):
        with mock.patch.object(h, "git_head", return_value="b" * 40):
            res, rh = self.run_h()
        self.assertEqual(res["status"], "BLOCKED")
        rh.assert_not_called()

    def test_unknown_revision_blocked(self):
        with mock.patch.object(h, "git_head", return_value=None):
            self.assertEqual(self.run_h()[0]["status"], "BLOCKED")

    def test_timeout_fail(self):
        def boom(cmd, timeout):
            raise subprocess.TimeoutExpired(cmd, timeout)
        self.assertEqual(self.run_h(boom)[0]["status"], "FAIL")

    def test_crash_fail(self):
        self.assertEqual(self.run_h(host_ok(rc=3))[0]["status"], "FAIL")

    def test_garbage_output_fail(self):
        self.assertEqual(self.run_h(host_ok(stdout="not json"))[0]["status"], "FAIL")

    def test_rejected_rom_fail(self):
        self.assertEqual(self.run_h(host_ok(loaded=False))[0]["status"], "FAIL")

    def test_not_mega_cd_mode_fail(self):
        self.assertEqual(self.run_h(host_ok(regions=("68KRAM",)))[0]["status"], "FAIL")

    def test_bad_expect_blocked(self):
        self.assertEqual(self.run_h(expects=("vram:0=00",))[0]["status"], "BLOCKED")

    def test_check_rom_and_parse_expect(self):
        self.assertEqual(h.check_rom(h.make_fixture()), ([], []))
        self.assertTrue(h.check_rom(h.make_fixture()[:0x10000])[1])  # size warning only
        bad = bytearray(h.make_fixture())
        bad[0x191] = ord("C")
        self.assertTrue(h.check_rom(bytes(bad))[0])
        self.assertEqual(h.parse_expect("main:FF0010=4F4B"), ("main", 0x10, b"OK"))
        self.assertEqual(h.parse_expect("prg:80001=00"), ("prg", 0x1, b"\0"))

    def test_lock_file_is_pinned(self):
        lock = h.read_lock()
        self.assertRegex(lock["commit"], r"^[0-9a-f]{40}$")
        self.assertTrue(lock["repo"].startswith("https://"))


class RealCore(unittest.TestCase):
    def test_fixture_boots_on_pinned_core(self):
        if not os.path.isfile(h.core_path(h.CACHE)):
            self.skipTest("pinned core not built (run: gpgx_harness.py fetch)")
        with tempfile.TemporaryDirectory() as d:
            rom = os.path.join(d, "fixture.bin")
            with open(rom, "wb") as fh:
                fh.write(h.make_fixture())
            ok = h.run(rom, expects=["main:FF0000=4F4B4F4B"], frames=30)
            self.assertEqual(ok["status"], "PASS", ok["reason"])
            bad = h.run(rom, expects=["main:FF0000=00000000"], frames=30)
            self.assertEqual(bad["status"], "FAIL", bad["reason"])


if __name__ == "__main__":
    unittest.main()
