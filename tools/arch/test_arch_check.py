"""Unit tests for arch_check.py using synthetic git repos in temp dirs.

Run: python -I -B -m unittest discover -s tools/arch -v
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import arch_check

REPO_RULES = Path(__file__).resolve().parents[2] / "arch" / "rules.toml"


class ArchCheckTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        self.write("arch/rules.toml", REPO_RULES.read_text("utf-8"))
        self.write("src/hw/vdp.inc", "VDP_CTRL equ $C00004\n")
        self.write("src/services/cd.s", '    include "../hw/vdp.inc"\n')
        self.write("src/boot/reset.s",
                   'reset:\n    .include "src/hw/vdp.inc"\n'
                   '    INCLUDE ../services/cd.s ; startup\n'
                   '; include "../../tests/never.s" (comment, ignored)\n')
        self.write("src/boot/Makefile", "ASFLAGS = -I src/hw\nOBJS = ../services/cd.s\n")
        self.write("tests/smoke/main.s", 'include "../../src/boot/reset.s"\n; runs under gpgx\n')
        self.write("tools/build.py", "print('x')\n")

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, "utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "-f", rel], check=True)

    def violations(self):
        return arch_check.check(self.root, self.root / "arch/rules.toml")

    def expect(self, fragment):
        v = self.violations()
        self.assertTrue(any(fragment in x for x in v), v)
        self.assertEqual(arch_check.main(["--root", str(self.root)]), 1)

    # positive
    def test_clean_layout_passes(self):
        self.assertEqual(self.violations(), [])
        self.assertEqual(arch_check.main(["--root", str(self.root)]), 0)

    def test_empty_repo_passes(self):
        shutil.rmtree(self.root / "src")
        shutil.rmtree(self.root / "tests")
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)
        self.assertEqual(self.violations(), [])

    # negative: forbidden edges
    def test_hw_must_not_depend_on_services(self):
        self.write("src/hw/bad.s", '    include "../services/cd.s"\n')
        self.expect("forbidden dependency hw -> services")

    def test_rom_must_not_depend_on_harness(self):
        self.write("src/services/bad.asm", '    incbin "tests/smoke/main.s"\n')
        self.expect("forbidden dependency services -> harness")

    def test_rom_must_not_depend_on_unlayered(self):
        self.write("src/hw/bad.inc", 'lbl: binclude "../../tools/build.py"\n')
        self.expect("depends on unlayered tools/build.py")

    def test_build_script_edge(self):
        self.write("src/hw/hw.mk", "SRC = src/services/cd.s\n")
        self.expect("forbidden dependency hw -> services")

    def test_unresolved_and_escaping_includes(self):
        self.write("src/hw/a.inc", '    include "missing.inc"\n')
        self.expect("does not resolve")
        self.write("src/hw/b.inc", '    include "../../../outside.inc"\n')
        self.expect("escapes the repository")
        self.write("src/hw/c.inc", '    include "/usr/share/x.inc"\n')
        self.expect("escapes the repository")

    def test_unassigned_src_file(self):
        self.write("src/misc/x.s", "    nop\n")
        self.expect("not assigned to any layer")

    def test_emulator_reference_in_rom(self):
        for i, text in enumerate(["; Genesis Plus GX hack\n", "IS_BLASTEM equ 1\n",
                                  "; picodrive workaround\n", "    dc.b 'libretro'\n"]):
            with self.subTest(text=text):
                self.write(f"src/boot/e{i}.s", text)
                self.expect(f"src/boot/e{i}.s:1: emulator-specific")

    def test_emulator_reference_in_rom_build_script(self):
        self.write("src/services/Makefile", "\nEMU = clownmdemu\n")
        self.expect("src/services/Makefile:2: emulator-specific")

    def test_gas_order_prefers_repo_root(self):
        self.write("tests/t.inc", "x equ 1\n")
        self.write("src/boot/tests/t.inc", "x equ 1\n")  # unassigned too, but root wins for the edge
        self.write("src/boot/g.s", '    .include "tests/t.inc"\n')
        self.expect("forbidden dependency boot -> harness (tests/t.inc)")

    # fail closed
    def test_missing_rules_fails_closed(self):
        self.assertEqual(arch_check.main(["--root", str(self.root), "--rules", str(self.root / "nope.toml")]), 2)

    def test_malformed_rules_fail_closed(self):
        good = REPO_RULES.read_text("utf-8")
        bad = [
            "version = [",
            good.replace("version = 1", "version = 2"),
            good.replace('hw = []\n', ""),                        # layer missing from [allow]
            good.replace('services = ["hw"]', 'services = ["gpu"]'),  # unknown layer
            good.replace("'clownmdemu'", "'('"),                  # bad regex
            good.replace("[scan]", "[scanx]"),
            good.replace("[rom_build]", "[rom_buildx]"),
            good.replace('targets = ["build/oss-mcd-bios.bin"]', 'targets = "build/x.bin"'),
        ]
        for i, body in enumerate(bad):
            with self.subTest(i=i):
                self.assertNotEqual(body, good)
                self.write("arch/rules.toml", body)
                self.assertEqual(arch_check.main(["--root", str(self.root)]), 2)

    def test_not_a_git_repo_fails_closed(self):
        bare = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, bare, ignore_errors=True)
        shutil.copytree(self.root / "arch", bare / "arch")
        self.assertEqual(arch_check.main(["--root", str(bare)]), 2)


MAKEFILE = """\
# synthetic, modeled on a typical GNU make ROM build
TC     ?= build/toolchain
CROSS   = $(TC)/bin/m68k-elf-
PYTHON ?= python3
ROM     = build/oss-mcd-bios.bin
.PHONY: all toolchain test
all: $(ROM)
toolchain:
\tbash tools/build/toolchain.sh $(TC)
build/boot.o: src/boot/reset.s | toolchain
\t$(CROSS)as -m68000 -I src/hw -o $@ $<
build/rom.elf: build/boot.o tools/build/rom.ld
\t$(CROSS)ld -T tools/build/rom.ld -o $@ build/boot.o
$(ROM): build/rom.elf tools/rom/mkrom.py
\t$(PYTHON) -I tools/rom/mkrom.py build/rom.elf $@
test:
\t$(PYTHON) tests/smoke/run.py --emulator gpgx
"""


class RomBuildTest(ArchCheckTest):
    test_empty_repo_passes = None  # removing src/ correctly breaks the ROM Makefile here

    def setUp(self):
        super().setUp()
        self.write("Makefile", MAKEFILE)
        self.write("tools/build/toolchain.sh", "echo pinned\n")
        self.write("tools/build/rom.ld", "OUTPUT_ARCH(m68k)\nENTRY(reset)\n")
        self.write("tools/rom/mkrom.py", "print('pad')\n")
        self.write("tests/smoke/run.py", "print('gpgx')\n")

    def patch(self, old, new):
        text = MAKEFILE.replace(old, new)
        self.assertNotEqual(text, MAKEFILE)
        self.write("Makefile", text)

    def test_harness_prerequisite_in_rom_rule(self):
        self.patch("src/boot/reset.s |", "src/boot/reset.s tests/smoke/main.s |")
        self.expect("ROM build depends on tests/smoke/main.s (harness)")

    def test_unlayered_tool_in_rom_recipe(self):
        self.write("tools/emu/hook.py", "x\n")
        self.patch("tools/rom/mkrom.py build/rom.elf", "tools/emu/hook.py build/rom.elf")
        self.expect("ROM build depends on tools/emu/hook.py (unlayered)")

    def test_harness_in_linker_script_input(self):
        self.write("tools/build/rom.ld", "INPUT(tests/smoke/main.s)\n")
        self.expect("ROM build depends on tests/smoke/main.s (harness)")

    def test_unresolved_linker_input(self):
        self.write("tools/build/rom.ld", "GROUP(missing.o)\n")
        self.expect("'missing.o' is neither a tracked file nor a target")

    def test_pattern_rule_reaching_harness(self):
        self.patch("build/boot.o: src/boot/reset.s | toolchain", "build/%.o: tests/smoke/%.s")
        self.write("tests/smoke/boot.s", "nop\n")
        self.expect("ROM build depends on tests/smoke/boot.s (harness)")

    def test_emulator_reference_via_variable(self):
        self.write("Makefile", MAKEFILE.replace("CROSS   =", "ASFLAGS = -DBLASTEM_FIX\nCROSS   =")
                   .replace("-m68000 -I", "$(ASFLAGS) -m68000 -I"))
        self.expect("emulator-specific reference 'BLASTEM' in ROM build input")

    def test_emulator_reference_in_build_tool(self):
        self.write("tools/rom/mkrom.py", "# detect picodrive\n")
        self.expect("tools/rom/mkrom.py: emulator-specific reference 'picodrive'")

    def test_missing_rom_target(self):
        self.patch("ROM     = build/oss-mcd-bios.bin", "ROM     = build/other.bin")
        self.expect("not defined (cannot verify ROM inputs)")

    def test_make_function_fails_closed(self):
        self.patch("build/boot.o tools/build/rom.ld", "build/boot.o $(wildcard tests/*.o)")
        self.expect("cannot analyze")

    def test_makefile_include_fails_closed(self):
        self.write("Makefile", "include extra.mk\n" + MAKEFILE)
        self.expect("include directives are not analyzed")

    def test_unresolved_prerequisite(self):
        self.patch("tools/rom/mkrom.py\n", "tools/rom/mkrom.py ghost.s\n")
        self.expect("'ghost.s' is neither a tracked file nor a target")


if __name__ == "__main__":
    unittest.main()
