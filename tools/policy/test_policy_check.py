"""Unit tests for policy_check.py using synthetic git repos in temp dirs.

Run: python -I -B -m unittest discover -s tools/policy -v
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import policy_check

REPO_POLICY = Path(__file__).resolve().parents[2] / "policy" / "allowlist.toml"


class PolicyCheckTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.git("init", "-q")
        self.write("policy/allowlist.toml", REPO_POLICY.read_bytes())
        self.write("README.md", b"# synthetic\nMentions Sega and SEGA in text.\n")
        self.write("src/boot/reset.s", b"; original synthetic code\n    nop\n")
        self.write("tests/fixtures/expected.txt", b"ok\n")
        self.write("tools/build.py", b"print('x')\n")
        self.commit()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "core.autocrlf=false", *args], check=True, capture_output=True)

    def write(self, rel, data):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def commit(self):
        self.git("add", "-A", "-f")
        self.git("commit", "-q", "-m", "c", "--allow-empty")

    def run_check(self, policy=None):
        return policy_check.main(["--root", str(self.root)] + (["--policy", policy] if policy else []))

    def violations(self):
        return policy_check.check(self.root, self.root / "policy/allowlist.toml")

    def add_and_expect(self, rel, data, fragment):
        self.write(rel, data)
        self.commit()
        v = self.violations()
        self.assertTrue(any(rel in x and fragment in x for x in v), v)
        self.assertEqual(self.run_check(), 1)

    # positive
    def test_clean_repo_passes(self):
        self.assertEqual(self.violations(), [])
        self.assertEqual(self.run_check(), 0)

    def test_markdown_text_with_md_extension_passes(self):
        self.write("docs/notes.md", "日本語 text\n".encode("utf-8"))
        self.commit()
        self.assertEqual(self.run_check(), 0)

    # negative
    def test_default_deny_unknown_location(self):
        self.add_and_expect("random/file.txt", b"hi\n", "default deny")

    def test_tracked_artifact_rejected(self):
        self.add_and_expect("build/out.lst", b"listing\n", "artifacts must not be tracked")

    def test_denied_extensions(self):
        for ext in (".bin", ".ROM", ".gen", ".iso", ".smd"):
            with self.subTest(ext=ext):
                self.add_and_expect(f"src/hw/x{ext}", b"text\n", "denied extension")

    def test_rom_header_in_md_file(self):
        rom = bytearray(0x200)
        rom[0x100:0x104] = b"SEGA"
        self.add_and_expect("tests/game.md", bytes(rom), "Mega Drive ROM header")

    def test_mega_cd_header(self):
        self.add_and_expect("src/boot/ip.s", b"SEGADISCSYSTEM  \x00\x01", "Mega-CD disc/boot header")

    def test_binary_and_non_utf8(self):
        self.add_and_expect("src/hw/a.inc", b"abc\x00def", "NUL byte")
        self.add_and_expect("src/hw/b.inc", b"\xff\xfe\x80", "not valid UTF-8")

    def test_oversize_file(self):
        self.add_and_expect("docs/huge.txt", b"a" * (1048576 + 1), "larger than")

    def test_untracked_and_ignored_inputs(self):
        self.write(".gitignore", b"*.lst\n")
        self.commit()
        self.write("src/new.s", b"nop\n")
        self.write("tools/cache.lst", b"x\n")  # ignored but still a build input
        self.write("notes.txt", b"outside inputs: not a violation\n")
        v = self.violations()
        self.assertTrue(any("src/new.s" in x for x in v), v)
        self.assertTrue(any("tools/cache.lst" in x for x in v), v)
        self.assertFalse(any("notes.txt" in x for x in v), v)

    def test_uncommitted_modification(self):
        self.write("src/boot/reset.s", b"; changed\n")
        self.assertTrue(any("uncommitted" in x for x in self.violations()))
        self.assertEqual(self.run_check(), 1)

    def test_uncommitted_policy_edit(self):
        p = self.root / "policy/allowlist.toml"
        p.write_bytes(p.read_bytes() + b"\n# loosened\n")
        self.assertTrue(any("policy/allowlist.toml" in x for x in self.violations()))

    # fail closed
    def test_missing_policy_fails_closed(self):
        self.assertEqual(self.run_check(str(self.root / "policy/nope.toml")), 2)

    def test_malformed_policy_fails_closed(self):
        for body in (b"not = [valid", b"version = 1\n", b"version = 2\n[locations]\n"):
            with self.subTest(body=body):
                self.write("policy/allowlist.toml", body)
                self.commit()
                self.assertEqual(self.run_check(), 2)

    def test_untracked_policy_fails_closed(self):
        self.write("policy/other.toml", REPO_POLICY.read_bytes())
        self.assertEqual(self.run_check(str(self.root / "policy/other.toml")), 2)

    def test_not_a_git_repo_fails_closed(self):
        bare = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, bare, ignore_errors=True)
        (bare / "policy").mkdir()
        (bare / "policy/allowlist.toml").write_bytes(REPO_POLICY.read_bytes())
        self.assertEqual(policy_check.main(["--root", str(bare)]), 2)


if __name__ == "__main__":
    unittest.main()
