"""Tests for tools/doctor/doctor.py against synthetic pin layouts (stdlib unittest).

Run: python -I -B -m unittest discover -s tests/host
fixtures/gpgx.lock is a verbatim copy of PR #15's tools/emu/gpgx.lock;
fixtures/toolchain.lock follows the agreed key=value format with tools/build/toolchain.sh values.
"""
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "doctor" / "doctor.py"
HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "golden"
FIXTURES = HERE / "fixtures"

_spec = importlib.util.spec_from_file_location("doctor", TOOL)
doctor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(doctor)

PY = Path(sys.executable).as_posix()  # contains '/', so doctor treats it as a path
PY_VERSION = platform.python_version()


class SyntheticRepo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def pin(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def fixture(self, name, rel):
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURES / name, self.root / rel)

    def rows(self, required=()):
        return {f"{r['group']}/{r['name']}": r for r in doctor.diagnose(self.root, set(required))}

    def status(self, required=()):
        return {k: r["status"] for k, r in self.rows(required).items()}

    def test_no_pins_is_skip_not_pass(self):
        self.assertEqual(self.status(), {"host/python": "PASS", "build/toolchain": "SKIP", "emu/gpgx": "SKIP"})
        self.assertTrue(all(r["reason"] for r in self.rows().values()))

    def test_required_missing_pins_fail(self):
        self.assertEqual(self.status({"build", "emu"}),
                         {"host/python": "PASS", "build/toolchain": "FAIL", "emu/gpgx": "FAIL"})

    def test_real_gpgx_lock_is_readable_and_not_checkable(self):
        """PR #15's gpgx.lock (repo/commit only) must not FAIL, even when emu is required."""
        self.fixture("gpgx.lock", "tools/emu/gpgx.lock")
        for required in ((), {"emu"}):
            r = self.rows(required)["emu/gpgx"]
            self.assertEqual(r["status"], "SKIP", r)
            self.assertIn("commit 87dd8b80802f", r["reason"])
            self.assertIn("not checkable", r["reason"])

    def test_toolchain_lock_missing_binary(self):
        self.fixture("toolchain.lock", "tools/build/toolchain.lock")
        r = self.rows()["build/binutils-m68k-elf"]
        self.assertEqual(r["status"], "SKIP")
        self.assertIn("m68k-elf-as not installed (pinned version 2.42)", r["reason"])
        r = self.rows({"build"})["build/binutils-m68k-elf"]
        self.assertEqual(r["status"], "FAIL")
        self.assertNotIn("toolchain", self.rows({"build"}))  # the pin is present, no 'absent' row

    def test_exact_version_match_passes(self):
        self.pin("tools/build/toolchain.lock", f"name=py\nversion={PY_VERSION}\ncommand={PY}\n")
        self.pin("tools/emu/gpgx.lock", f"version={PY_VERSION}\ncommand={PY}\nversion_cmd={PY} -V\n")
        self.assertEqual(self.status({"build", "emu"}), {"host/python": "PASS", "build/py": "PASS", "emu/gpgx": "PASS"})

    def test_version_is_exact_not_substring(self):
        prefix = PY_VERSION.rsplit(".", 1)[0]  # "3.14" is a substring of "3.14.3" but not equal
        self.pin("tools/build/toolchain.lock", f"version={prefix}\ncommand={PY}\n")
        r = self.rows()["build/toolchain"]
        self.assertEqual(r["status"], "FAIL")
        self.assertIn(f"expected version {prefix!r}", r["reason"])

    def test_failing_version_command_fails(self):
        self.pin("tools/build/toolchain.lock", f"version={PY_VERSION}\ncommand={PY}\nversion_cmd={PY} -c \"raise SystemExit(3)\"\n")
        self.assertEqual(self.status()["build/toolchain"], "FAIL")

    def test_installed_without_version_key_is_skip(self):
        self.pin("tools/build/toolchain.lock", f"command={PY}\nsha256={'0' * 64}\n")
        r = self.rows({"build"})["build/toolchain"]
        self.assertEqual(r["status"], "SKIP")
        self.assertIn("no version key", r["reason"])

    def test_unreadable_pins_fail_even_when_optional(self):
        for text in ("{\"json\": 1}\n", "version 1.0\n", "# only comments\n", "a=1\na=2\n"):
            self.pin("tools/emu/gpgx.lock", text)
            r = self.rows()["emu/gpgx"]
            self.assertEqual(r["status"], "FAIL", text)
            self.assertIn("unreadable", r["reason"])

    def test_secondary_emulator_pins_are_checked(self):
        self.fixture("gpgx.lock", "tools/emu/gpgx.lock")
        self.pin("tools/emu/picodrive.lock", "name=picodrive\nversion=2.0\ncommand=definitely-not-installed-picodrive\n")
        self.assertEqual(self.status()["emu/picodrive"], "SKIP")
        self.assertEqual(self.status({"emu"})["emu/picodrive"], "FAIL")

    def test_old_python_fails(self):
        r = doctor.diagnose(self.root, set(), python_version=(3, 10, 0))[0]
        self.assertEqual((r["name"], r["status"]), ("python", "FAIL"))

    def test_golden_report(self):
        self.fixture("gpgx.lock", "tools/emu/gpgx.lock")
        self.fixture("toolchain.lock", "tools/build/toolchain.lock")
        rows = [r for r in doctor.diagnose(self.root, set()) if r["group"] != "host"]
        actual = json.dumps(rows, indent=2) + "\n"
        path = GOLDEN / "doctor_report.json"
        if os.environ.get("UPDATE_GOLDEN"):
            path.write_text(actual, encoding="utf-8", newline="\n")
        self.assertEqual(actual, path.read_text(encoding="utf-8"))

    def test_cli_exit_codes(self):
        def cli(*args):
            return subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--root", str(self.root), *args],
                                  capture_output=True, text=True)
        self.fixture("gpgx.lock", "tools/emu/gpgx.lock")
        ok = cli()
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("SKIP is not success", ok.stdout)
        self.assertEqual(cli("--require", "emu").returncode, 0)    # real gpgx.lock: SKIP, not FAIL
        self.assertEqual(cli("--require", "build").returncode, 1)  # toolchain.lock absent
        self.assertEqual(cli("--require", "nope").returncode, 2)
        self.assertEqual({r["status"] for r in json.loads(cli("--json").stdout)}, {"PASS", "SKIP"})
        self.pin("tools/emu/gpgx.lock", "garbage\n")
        self.assertEqual(cli().returncode, 1)  # unreadable pin fails tier 1


if __name__ == "__main__":
    unittest.main()
