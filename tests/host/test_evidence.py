"""Tests for tools/evidence/evidence.py (stdlib unittest).

Run: python -I -B -m unittest discover -s tests/host
Set UPDATE_GOLDEN=1 to rewrite golden files (review the diff before committing).
"""
import copy
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "evidence" / "evidence.py"
SCHEMA = ROOT / "tools" / "evidence" / "result.schema.json"
GOLDEN = Path(__file__).resolve().parent / "golden"

_spec = importlib.util.spec_from_file_location("evidence", TOOL)
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)

FIXTURE_SHA256 = hashlib.sha256(ev.synthetic_rom()).hexdigest()
ENV = {"os": "linux", "arch": "x86_64", "python": "3.12.0"}
EMU_SHA = "0123456789abcdef0123456789abcdef01234567"


def rec(status="PASS", checkpoint="startup", **kw):
    defaults = dict(rom_sha256=FIXTURE_SHA256, emulator_id="gpgx", emulator_sha=EMU_SHA,
                    environment=ENV, observed={"checkpoint": "reset-loop", "pc": "0x000204"})
    if checkpoint == "rom-built":
        defaults.update(emulator_id="none", emulator_sha=None, observed={})
    if status != "PASS":
        defaults["reason"] = "synthetic reason"
    defaults.update(kw)
    return ev.make_record(status, checkpoint, **defaults)


def golden(name, actual):
    path = GOLDEN / name
    if os.environ.get("UPDATE_GOLDEN"):
        path.parent.mkdir(exist_ok=True)
        path.write_text(actual, encoding="utf-8", newline="\n")
    return path.read_text(encoding="utf-8")


def run_cli(*args):
    return subprocess.run([sys.executable, "-I", "-B", str(TOOL), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


class SyntheticFixture(unittest.TestCase):
    def test_deterministic_and_original(self):
        rom = ev.synthetic_rom()
        self.assertEqual(rom, ev.synthetic_rom())
        self.assertEqual(len(rom), 0x20000)
        ssp, pc = struct.unpack_from(">II", rom, 0)
        self.assertEqual((ssp, pc), (0x00FFFD00, 0x200))
        self.assertEqual(rom[pc:pc + 6], bytes.fromhex("46FC270060FE"))
        self.assertIn(ev.FIXTURE_MARKER, rom)
        self.assertNotIn(b"SEGA", rom.upper())  # no third-party identifiers

    def test_fixture_hash_is_golden(self):
        self.assertEqual(FIXTURE_SHA256, golden("fixture.sha256", FIXTURE_SHA256 + "\n").strip())


class Validation(unittest.TestCase):
    def test_valid_records(self):
        for r in (rec(), rec("PASS", "rom-built"), rec("SKIP", rom_sha256=None, emulator_sha=None, observed={}),
                  rec("PASS", emulator_id="hardware:mega-cd-model1", emulator_sha=None)):
            self.assertEqual(ev.validate(r), [], r)

    def test_rejections(self):
        cases = {
            "SKIP requires a non-empty reason": rec("SKIP", reason=None),
            "BLOCKED requires a non-empty reason": rec("BLOCKED", reason=""),
            "PASS requires rom_sha256": rec(rom_sha256=None),
            "build-only is not a boot": rec("PASS", "startup", emulator_id="none"),
            "rom-built records must use emulator.id 'none'": rec("PASS", "rom-built", emulator_id="gpgx"),
            "runtime PASS requires observed state": rec(observed={}),
            "requires a pinned emulator.sha": rec(emulator_sha=None),
            "status must be one of": rec(status="OK"),
            "rom_sha256 must be": rec(rom_sha256="ABC"),
        }
        for expected, r in cases.items():
            self.assertTrue(any(expected in e for e in ev.validate(r)), (expected, ev.validate(r)))
        broken = rec()
        broken["extra"] = 1
        del broken["reason"]
        self.assertEqual(ev.validate(broken), ["missing field: reason", "unknown field: extra"])
        self.assertEqual(ev.validate([]), ["record is not an object"])


class SchemaDifferential(unittest.TestCase):
    """The JSON Schema and the stdlib validator must agree on the contract."""

    def test_schema_matches_validator_constants(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        props = schema["properties"]
        self.assertEqual(tuple(schema["required"]), ev.REQUIRED)
        self.assertEqual(set(props), set(ev.REQUIRED))
        self.assertEqual(tuple(props["status"]["enum"]), ev.STATUSES)
        self.assertEqual(tuple(props["checkpoint"]["enum"]), ev.CHECKPOINTS)
        self.assertEqual(props["schema_version"]["const"], ev.SCHEMA_VERSION)
        self.assertEqual(props["log_excerpt"]["maxLength"], ev.LOG_MAX_CHARS)
        self.assertEqual(props["rom_sha256"]["pattern"], ev._SHA256.pattern)
        self.assertEqual(props["emulator"]["properties"]["id"]["pattern"], ev._EMU_ID.pattern)
        self.assertEqual(props["emulator"]["properties"]["sha"]["pattern"], ev._EMU_SHA.pattern)

    def test_checkpoints_match_compatibility_doc(self):
        doc = (ROOT / "docs" / "compatibility.md").read_text(encoding="utf-8")
        stages = [line.split("|")[1].strip().lower() for line in doc.splitlines()
                  if line.startswith("| ") and not line.startswith(("| Stage", "| ---"))]
        self.assertEqual(tuple(stages[:len(ev.CHECKPOINTS)]), ev.CHECKPOINTS)


class Sanitizer(unittest.TestCase):
    def test_strips_paths_secrets_and_controls(self):
        log = ("boot at C:\\Users\\alice\\rom.bin\r\nopen /home/alice/x.bin ok\n"
               "GITHUB_TOKEN=ghp_abcdef password: hunter2\x07\nPC=0x000204 /dev/null\n")
        out = ev.sanitize(log)
        for leaked in ("alice", "ghp_abcdef", "hunter2", "\x07", "\r"):
            self.assertNotIn(leaked, out)
        self.assertIn("<path>", out)
        self.assertIn("TOKEN=<redacted>", out)
        self.assertIn("PC=0x000204 /dev/null", out)

    def test_leak_regressions(self):
        cases = {
            "Authorization: Bearer abc.def.ghi": ("abc.def.ghi", "Bearer"),
            "curl -H 'Authorization: Basic dXNlcjpwYXNz'": ("dXNlcjpwYXNz",),
            "header bearer eyJhbGciOi.payload.sig": ("eyJhbGciOi",),
            "pushed with ghp_ABCDEFGHIJKLMNOPQRST0123456789": ("ghp_ABCDEF",),
            "pat github_pat_11ABCDEFG0123456789_abcdefghij": ("github_pat_11",),
            "glpat-abcdefghij0123456789 xoxb-1234567890-abcdef AKIAABCDEFGHIJKLMNOP": ("glpat-", "xoxb-", "AKIA"),
            "clone https://user:s3cret@github.com/o/r.git": ("user:", "s3cret"),
            "at /__w/oss-mcd-bios/oss-mcd-bios/build/rom.bin": ("/__w", "oss-mcd-bios/build"),
            "cwd /srv/ci/job and /workspace/repo/x.log": ("/srv", "/workspace", "ci/job"),
            "home ~/projects/rom.bin and \\\\fileserver\\share\\rom.bin": ("projects", "fileserver"),
        }
        for log, leaks in cases.items():
            out = ev.sanitize(log)
            for leaked in leaks:
                self.assertNotIn(leaked, out, (log, out))
        # Non-sensitive content survives.
        kept = ev.sanitize("PC=0x000204 I/O ok 10/08 https://example.org/doc /dev/null sha " + FIXTURE_SHA256)
        for part in ("PC=0x000204", "I/O", "10/08", "https://example.org/doc", "/dev/null", FIXTURE_SHA256):
            self.assertIn(part, kept)

    def test_keeps_bounded_tail(self):
        out = ev.sanitize("\n".join(f"line {i}" for i in range(1000)))
        self.assertEqual(out.splitlines()[-1], "line 999")
        self.assertEqual(len(out.splitlines()), ev.LOG_MAX_LINES)
        self.assertLessEqual(len(ev.sanitize("x" * 10000)), ev.LOG_MAX_CHARS)


class Aggregation(unittest.TestCase):
    def agg(self, *records):
        return ev.aggregate([(f"r{i}.json", r) for i, r in enumerate(records)])

    def test_skip_and_blocked_are_never_success(self):
        s = self.agg(rec("SKIP"), rec("BLOCKED", "bios-loaded"))
        self.assertEqual(s["success_cells"], 0)
        self.assertEqual(s["cells"]["startup"]["gpgx"], "SKIP")
        self.assertEqual(s["cells"]["bios-loaded"]["gpgx"], "BLOCKED")

    def test_build_only_never_yields_boot_pass(self):
        s = self.agg(rec("PASS", "rom-built"))
        self.assertEqual(s["cells"]["rom-built"]["none"], "PASS")
        self.assertEqual(s["emulators"], ["none"])
        for cp in ev.CHECKPOINTS[1:]:
            self.assertEqual(s["cells"][cp]["none"], "UNTESTED")
        # A forged "boot PASS" without an emulator is invalid and counts as FAIL.
        forged = rec("PASS", "rom-built")
        forged["checkpoint"] = "homebrew-boot"
        s = self.agg(forged)
        self.assertEqual(s["cells"]["homebrew-boot"]["none"], "FAIL")
        self.assertEqual(s["success_cells"], 0)
        self.assertEqual(len(s["invalid"]), 1)

    def test_precedence_and_unreadable(self):
        s = self.agg(rec(), rec("FAIL"), rec("SKIP"))
        self.assertEqual(s["cells"]["startup"]["gpgx"], "FAIL")
        s = self.agg(rec(), rec("SKIP"), ("bad.json", None))
        self.assertEqual(s["cells"]["startup"]["gpgx"], "PASS")
        self.assertEqual(s["cells"]["rom-built"]["none"], "FAIL")

    def test_emulator_differential(self):
        """Disagreeing emulators stay separate columns; one PASS never covers the other."""
        s = self.agg(rec(), rec("FAIL", emulator_id="picodrive"))
        self.assertEqual(s["cells"]["startup"], {"gpgx": "PASS", "picodrive": "FAIL"})

    def test_input_order_independent(self):
        records = [rec(), rec("FAIL", "bios-loaded"), rec("PASS", "rom-built"), rec("SKIP", emulator_id="picodrive")]
        a = self.agg(*records)
        b = self.agg(*reversed(copy.deepcopy(records)))
        self.assertEqual(a["cells"], b["cells"])


class Golden(unittest.TestCase):
    def test_record(self):
        actual = json.dumps(rec(log="PC=0x000204\n"), indent=2, sort_keys=True) + "\n"
        self.assertEqual(actual, golden("record_startup_pass.json", actual))

    def test_matrix(self):
        s = ev.aggregate([("a", rec("PASS", "rom-built")), ("b", rec()), ("c", rec("SKIP", emulator_id="picodrive")),
                          ("d", rec("BLOCKED", "disc-detected"))])
        actual = ev.render_matrix(s) + "\n"
        self.assertEqual(actual, golden("matrix_mixed.md", actual))

    def test_empty_matrix_has_no_contradictory_counts(self):
        text = ev.render_matrix(ev.aggregate([]))
        self.assertIn("every stage is UNTESTED (no record)", text)
        self.assertNotIn("UNTESTED 0", text)

    def test_update_doc_only_touches_generated_section(self):
        doc = f"head\n{ev.BEGIN_MARK}\nold\n{ev.END_MARK}\ntail\n"
        self.assertEqual(ev.update_doc(doc, "NEW"), f"head\n{ev.BEGIN_MARK}\nNEW\n{ev.END_MARK}\ntail\n")
        for bad in ("no markers", f"{ev.END_MARK}\n{ev.BEGIN_MARK}", doc + doc):
            with self.assertRaises(ValueError):
                ev.update_doc(bad, "x")


class EndToEnd(unittest.TestCase):
    """Drive the CLI as CI does: fixture -> collect -> validate -> aggregate -> matrix."""

    def test_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            out = run_cli("fixture", "--out", tmp / "fixture.bin")
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(out.stdout.strip(), FIXTURE_SHA256)
            (tmp / "run.log").write_text(f"loaded {tmp / 'fixture.bin'}\nreset ok\n", encoding="utf-8")
            recs = tmp / "records"
            ok = run_cli("collect", "--status", "PASS", "--checkpoint", "rom-built", "--rom", tmp / "fixture.bin",
                         "--log", tmp / "run.log", "--out", recs / "built.json")
            self.assertEqual(ok.returncode, 0, ok.stderr)
            built = json.loads((recs / "built.json").read_text(encoding="utf-8"))
            self.assertEqual(built["rom_sha256"], FIXTURE_SHA256)
            self.assertNotIn(str(tmp), json.dumps(built))
            skip = run_cli("collect", "--status", "SKIP", "--checkpoint", "startup", "--emulator-id", "gpgx",
                           "--reason", "tools/emu/gpgx.lock absent", "--out", recs / "gpgx.json")
            self.assertEqual(skip.returncode, 0, skip.stderr)
            # Build-only PASS claimed as a boot is refused and nothing is written.
            refused = run_cli("collect", "--status", "PASS", "--checkpoint", "homebrew-boot",
                              "--rom", tmp / "fixture.bin", "--out", recs / "forged.json")
            self.assertEqual(refused.returncode, 2)
            self.assertFalse((recs / "forged.json").exists())

            self.assertEqual(run_cli("validate", recs).returncode, 0)
            agg = run_cli("aggregate", recs, "--fail-on-fail")
            self.assertEqual(agg.returncode, 0, agg.stderr)
            summary = json.loads(agg.stdout)
            self.assertEqual(summary["success_cells"], 1)
            self.assertEqual(summary["cells"]["startup"]["gpgx"], "SKIP")

            doc = tmp / "compat.md"
            doc.write_text(f"intro\n{ev.BEGIN_MARK}\n{ev.END_MARK}\nrest\n", encoding="utf-8")
            self.assertEqual(run_cli("matrix", recs, "--doc", doc, "--check").returncode, 1)
            self.assertEqual(run_cli("matrix", recs, "--doc", doc).returncode, 0)
            self.assertEqual(run_cli("matrix", recs, "--doc", doc, "--check").returncode, 0)
            text = doc.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("intro\n") and text.endswith("rest\n"))
            self.assertIn("| startup | UNTESTED | SKIP |", text)

            (recs / "bad.json").write_text("{not json", encoding="utf-8")
            self.assertEqual(run_cli("validate", recs).returncode, 1)
            self.assertEqual(run_cli("aggregate", recs, "--fail-on-fail").returncode, 1)

    def test_validate_fails_closed_on_missing_or_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_cli("validate", Path(tmp) / "nope").returncode, 1)
            self.assertEqual(run_cli("validate", tmp).returncode, 1)  # zero records is not success
            ok = Path(tmp) / "ok.json"
            ok.write_text(json.dumps(rec()), encoding="utf-8")
            self.assertEqual(run_cli("validate", tmp).returncode, 0)
            self.assertEqual(run_cli("validate", tmp, Path(tmp) / "nope").returncode, 1)

    def test_repository_doc_is_in_sync(self):
        self.assertEqual(run_cli("matrix", "--doc", ROOT / "docs" / "compatibility.md", "--check").returncode, 0)


if __name__ == "__main__":
    unittest.main()
