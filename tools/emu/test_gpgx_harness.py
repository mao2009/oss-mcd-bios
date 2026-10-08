"""Unit tests for gpgx_harness.py. The emulator process boundary (run_host/git_head) is mocked.

  python -I tools/emu/test_gpgx_harness.py
RealCore runs the pinned core only if `gpgx_harness.py fetch` has been run; otherwise it skips.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True  # no untracked __pycache__ inside the repository
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpgx_harness as h  # noqa: E402

PIN = "a" * 40
LOCK = {"name": "gpgx", "version": "v1.7.4", "url": "https://example.invalid/gpgx", "commit": PIN}
RECORD_KEYS = {"schema_version", "status", "checkpoint", "rom_sha256", "rom_commit", "emulator",
               "environment", "observed", "log_excerpt", "reason"}


def fake_host(final=b"OKOK", power_on=b"\0\0\0\0", regions=("68KRAM", "PRGRAM"), loaded=True, rc=0, stdout=None):
    """Fake child host: writes main.init.bin / main.bin into the workdir it was given (cmd[6])."""
    def fake(cmd, timeout):
        for name, data in (("main.init.bin", power_on), ("main.bin", final)):
            with open(os.path.join(cmd[6], name), "wb") as fh:
                fh.write(data.ljust(0x10000, b"\0"))
        out = stdout if stdout is not None else json.dumps(
            {"loaded": loaded, "regions": list(regions), "frames_run": int(cmd[5]), "samples": [],
             "core_log": ["[1] loading C:\\Users\\someone\\x.bin"]})
        return subprocess.CompletedProcess(cmd, rc, out, "")
    return fake


class Harness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rom = os.path.join(self.tmp.name, "rom.bin")
        self.write_rom(h.make_fixture())
        self.gpgx = os.path.join(self.tmp.name, "gpgx")
        os.makedirs(self.gpgx)
        open(h.core_path(self.gpgx), "wb").close()
        p = mock.patch.object(h, "git_head", return_value=PIN)
        p.start()
        self.addCleanup(p.stop)

    def write_rom(self, data):
        with open(self.rom, "wb") as fh:
            fh.write(data)

    def run_h(self, fake=None, expects=("main:FF0000=4F4B4F4B",), rom=None, mode="system", lock=LOCK):
        with mock.patch.object(h, "run_host", side_effect=fake or fake_host()) as rh:
            rec = h.run(rom or self.rom, self.gpgx, 10, list(expects), lock=lock, mode=mode)
        self.assertEqual(set(rec), RECORD_KEYS)
        self.assertEqual(set(rec["emulator"]), {"id", "version", "sha"})
        self.assertEqual(rec["schema_version"], 1)
        self.assertTrue(rec["reason"])
        self.assertNotIn(self.tmp.name, json.dumps(rec).replace("\\\\", "\\"))  # no absolute paths
        return rec, rh

    def test_pass_when_checkpoint_holds(self):
        rec, rh = self.run_h()
        self.assertEqual((rec["status"], rec["checkpoint"]), ("PASS", "startup"))
        self.assertEqual(rec["emulator"], {"id": "gpgx", "version": "v1.7.4", "sha": PIN})
        self.assertEqual(len(rec["rom_sha256"]), 64)
        self.assertIn("<path>", rec["log_excerpt"])
        self.assertTrue(rh.call_args[0][0][4].endswith("disc.iso"))  # system mode boots a blank disc

    def test_do_nothing_bios_cannot_pass_with_power_on_value(self):
        rec, _ = self.run_h(fake_host(final=b"\0\0\0\0"), expects=("main:FF0000=00000000",))
        self.assertEqual(rec["status"], "FAIL")
        self.assertIn("power-on", rec["reason"])

    def test_fail_when_checkpoint_differs(self):
        self.assertEqual(self.run_h(fake_host(final=b"NOPE"))[0]["status"], "FAIL")

    def test_no_expect_never_pass(self):
        rec, rh = self.run_h(expects=())
        self.assertNotEqual(rec["status"], "PASS")
        self.assertEqual((rec["status"], rec["checkpoint"]), ("BLOCKED", "bios-loaded"))
        rh.assert_called_once()

    def test_system_mode_needs_no_header(self):
        rom = bytearray(h.make_fixture())
        rom[0x180:0x182] = b"  "
        self.write_rom(bytes(rom))
        self.assertEqual(self.run_h()[0]["status"], "PASS")
        rec, rh = self.run_h(mode="bootrom")
        self.assertEqual(rec["status"], "BLOCKED")
        self.assertIn("'BR'", rec["reason"])
        rh.assert_not_called()

    def test_bootrom_mode_passes_rom_as_content(self):
        rec, rh = self.run_h(mode="bootrom")
        self.assertEqual(rec["status"], "PASS")
        self.assertTrue(rh.call_args[0][0][4].endswith("bios.bin"))

    def test_missing_rom_blocked(self):
        rec, rh = self.run_h(rom=os.path.join(self.tmp.name, "nope.bin"))
        self.assertEqual(rec["status"], "BLOCKED")
        self.assertIsNone(rec["rom_sha256"])
        rh.assert_not_called()

    def test_missing_lock_blocked(self):
        with mock.patch.object(h, "LOCK", os.path.join(self.tmp.name, "missing.lock")):
            rec, rh = self.run_h(lock=None)
        self.assertEqual(rec["status"], "BLOCKED")
        self.assertIn("lock", rec["reason"])
        rh.assert_not_called()

    def test_lock_without_commit_blocked(self):
        self.assertEqual(self.run_h(lock={"name": "gpgx"})[0]["status"], "BLOCKED")

    def test_missing_core_skip(self):
        os.remove(h.core_path(self.gpgx))
        rec, rh = self.run_h()
        self.assertEqual(rec["status"], "SKIP")
        rh.assert_not_called()

    def test_wrong_revision_blocked(self):
        with mock.patch.object(h, "git_head", return_value="b" * 40):
            rec, rh = self.run_h()
        self.assertEqual(rec["status"], "BLOCKED")
        rh.assert_not_called()

    def test_unknown_revision_blocked(self):
        with mock.patch.object(h, "git_head", return_value=None):
            self.assertEqual(self.run_h()[0]["status"], "BLOCKED")

    def test_timeout_fail(self):
        def boom(cmd, timeout):
            raise subprocess.TimeoutExpired(cmd, timeout)
        self.assertEqual(self.run_h(boom)[0]["status"], "FAIL")

    def test_crash_fail(self):
        self.assertEqual(self.run_h(fake_host(rc=3))[0]["status"], "FAIL")

    def test_garbage_output_fail(self):
        self.assertEqual(self.run_h(fake_host(stdout="not json"))[0]["status"], "FAIL")

    def test_rejected_rom_fail(self):
        self.assertEqual(self.run_h(fake_host(loaded=False))[0]["status"], "FAIL")

    def test_not_mega_cd_mode_fail(self):
        self.assertEqual(self.run_h(fake_host(regions=("68KRAM",)))[0]["status"], "FAIL")

    def test_bad_expect_blocked(self):
        for bad in ("vram:0=00", "main:00FF00=00", "main:FFFFFE=00000000", "prg:080000=00", "main:FF0000="):
            self.assertEqual(self.run_h(expects=(bad,))[0]["status"], "BLOCKED", bad)

    def test_check_rom_and_parse_expect(self):
        self.assertEqual(h.check_rom(h.make_fixture(), "bootrom"), ([], []))
        self.assertTrue(h.check_rom(h.make_fixture()[:0x10000], "system")[1])  # size warning only
        bad = bytearray(h.make_fixture())
        bad[0x191] = ord("C")
        self.assertTrue(h.check_rom(bytes(bad), "bootrom")[0])
        self.assertEqual(h.check_rom(bytes(bad), "system")[0], [])
        self.assertEqual(h.parse_expect("main:FF0010=4F4B"), ("main", 0x10, b"OK"))
        self.assertEqual(h.parse_expect("prg:07FFFF=00"), ("prg", 0x7FFFF, b"\0"))

    def test_lock_file_has_shared_keys(self):
        lock = h.read_lock()
        self.assertLessEqual({"name", "version", "url", "commit", "command", "version_cmd"}, set(lock))
        self.assertRegex(lock["commit"], r"^[0-9a-f]{40}$")
        self.assertTrue(lock["url"].startswith("https://"))

    def test_cache_dir_outside_repo(self):
        repo = os.path.dirname(os.path.dirname(h.HERE))
        with mock.patch.dict(os.environ, {"GPGX_CACHE_DIR": self.tmp.name}):
            self.assertEqual(h.cache_dir(), self.tmp.name)
        with mock.patch.dict(os.environ):
            os.environ.pop("GPGX_CACHE_DIR", None)
            self.assertFalse(os.path.abspath(h.cache_dir()).startswith(repo + os.sep))


class RealCore(unittest.TestCase):
    def setUp(self):
        if not os.path.isfile(h.core_path(h.cache_dir())):
            self.skipTest("pinned core not built (run: gpgx_harness.py fetch)")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def rom(self, data):
        path = os.path.join(self.tmp.name, "r.bin")
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def test_fixture_boots_on_pinned_core(self):
        no_br = bytearray(h.make_fixture())
        no_br[0x180:0x182] = b"  "
        for mode, data in (("system", bytes(no_br)), ("bootrom", h.make_fixture())):
            rec = h.run(self.rom(data), expects=["main:FF0000=4F4B4F4B"], frames=30, mode=mode)
            self.assertEqual(rec["status"], "PASS", (mode, rec["reason"]))

    def test_do_nothing_rom_fails(self):
        idle = bytearray(h.make_fixture())
        idle[0x200:0x20C] = bytes.fromhex("60FE") * 6  # never writes anything
        rec = h.run(self.rom(bytes(idle)), expects=["main:FF0000=00000000"], frames=30)
        self.assertEqual(rec["status"], "FAIL", rec["reason"])
        rec = h.run(self.rom(bytes(idle)), expects=["main:FF0000=4F4B4F4B"], frames=30)
        self.assertEqual(rec["status"], "FAIL", rec["reason"])


if __name__ == "__main__":
    unittest.main()
