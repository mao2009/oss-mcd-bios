"""Pinned Genesis Plus GX smoke-test harness (external, test-only; stdlib only).

  python -I tools/emu/gpgx_harness.py fetch                 # clone + build the pinned core
  python -I tools/emu/gpgx_harness.py make-fixture OUT.bin  # tiny synthetic test ROM
  python -I tools/emu/gpgx_harness.py run --rom BIOS.bin --expect main:FF0000=4F4B4F4B

`run` emits {status, rom_sha256, emulator_sha, command, trace, reason}.
status: PASS (every --expect held) | FAIL | SKIP (emulator not built) | BLOCKED (cannot judge).
Never PASS without at least one checkpoint assertion. Exit code: PASS 0, FAIL 1, SKIP 3, BLOCKED 4.
"""
import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(HERE, "gpgx.lock")
CACHE = os.path.join(HERE, ".cache", "gpgx")
HOST = os.path.join(HERE, "libretro_host.py")
EXIT = {"PASS": 0, "FAIL": 1, "SKIP": 3, "BLOCKED": 4}
SPACES = {"main": 0xFFFF, "prg": 0x7FFFF}  # 68K RAM $FF0000 (64KB), sub-CPU PRG-RAM $000000 (512KB)
BOOTROM_SIZE = 0x20000


def read_lock(path=LOCK):
    with open(path, encoding="utf-8") as fh:
        pairs = (line.split("=", 1) for line in fh if "=" in line and not line.startswith("#"))
        return {k.strip(): v.strip() for k, v in pairs}


def core_path(gpgx_dir):
    ext = {"win32": "dll", "darwin": "dylib"}.get(sys.platform, "so")
    return os.path.join(gpgx_dir, f"genesis_plus_gx_libretro.{ext}")


def git_head(gpgx_dir):
    try:
        out = subprocess.run(["git", "-C", gpgx_dir, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def check_rom(data):
    """Loader preconditions of the pinned core for booting a ROM as a CD BOOT ROM.

    See docs/emulator/gpgx-investigation.md (core/loadrom.c load_rom()). Returns (blockers, warnings).
    """
    blockers, warnings = [], []
    if not data:
        return ["ROM is empty"], warnings
    if len(data) > 0x800000:
        blockers.append("ROM larger than 8MB; core only treats <=8MB images as BOOT ROM")
    if data[0x180:0x182] != b"BR":
        blockers.append("header $180 is not 'BR'; core would not map the image as CD BOOT ROM")
    if b"C" in data[0x190:0x19E]:
        blockers.append("I/O support field $190 contains 'C'; core would boot it as a Mode 1 cartridge")
    if b"FLUX" in data[0x120:0x150]:
        blockers.append("domestic name contains 'FLUX'; core would boot it as a Mode 1 cartridge")
    if b"SEGA PICO" in data[0x100:0x110]:
        blockers.append("console name contains 'SEGA PICO'; core would select Pico hardware")
    if data[0x100:0x104] != b"SEGA" and len(data) % 512 == 0 and (len(data) // 512) % 2:
        blockers.append("core would strip a 512-byte copier header (no 'SEGA' at $100, odd 512-byte count)")
    if len(data) != BOOTROM_SIZE:
        warnings.append(f"ROM size {len(data):#x} != {BOOTROM_SIZE:#x}; core copies exactly 128KB into BOOT ROM")
    return blockers, warnings


def parse_expect(text):
    """'main:FF0000=4F4B' -> ('main', 0x0000, b'OK')."""
    loc, value = text.split("=", 1)
    space, addr = loc.split(":", 1)
    if space not in SPACES:
        raise ValueError(f"unknown space {space!r} in {text!r} (use main or prg)")
    want = bytes.fromhex(value)
    if not want:
        raise ValueError(f"empty expected value in {text!r}")
    return space, int(addr, 16) & SPACES[space], want


def make_fixture():
    """128KB synthetic ROM, hand-assembled here: writes 'OKOK' to $FF0000 then loops forever."""
    rom = bytearray(BOOTROM_SIZE)
    rom[0:8] = bytes.fromhex("00FFFE00 00000200")             # reset SSP, reset PC
    rom[8:0x100] = bytes.fromhex("0000020A") * 62             # other vectors -> idle loop
    rom[0x100:0x200] = b" " * 0x100
    rom[0x100:0x110] = b"SEGA MEGA DRIVE "
    rom[0x120:0x13C] = b"OSS-MCD-BIOS HARNESS FIXTURE"
    rom[0x180:0x182] = b"BR"
    rom[0x190] = ord("J")
    rom[0x1F0] = ord("U")
    rom[0x200:0x20C] = bytes.fromhex("23FC 4F4B4F4B 00FF0000"   # move.l #'OKOK',($FF0000).l
                                     "60FE")                   # bra.s *
    return bytes(rom)


def run_host(cmd, timeout):
    """The executable boundary (mocked in unit tests)."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def run(rom, gpgx_dir=CACHE, frames=120, expects=(), region="auto", timeout=120, lock=None):
    lock = lock or read_lock()
    res = {"status": "BLOCKED", "rom_sha256": None, "emulator_sha": None, "command": None,
           "trace": {"pinned_sha": lock.get("commit"), "frames_requested": frames}, "reason": None}

    def done(status, reason):
        res.update(status=status, reason=reason)
        return res

    try:
        with open(rom, "rb") as fh:
            data = fh.read()
    except OSError as e:
        return done("BLOCKED", f"BIOS ROM not readable: {e}")
    res["rom_sha256"] = hashlib.sha256(data).hexdigest()
    blockers, warnings = check_rom(data)
    res["trace"]["rom_warnings"] = warnings
    if blockers:
        return done("BLOCKED", "; ".join(blockers))
    try:
        checks = [parse_expect(e) for e in expects]
    except ValueError as e:
        return done("BLOCKED", f"bad --expect: {e}")

    core = core_path(gpgx_dir)
    if not os.path.isfile(core):
        return done("SKIP", f"emulator core not found at {core}; run: python -I {__file__} fetch")
    sha = git_head(gpgx_dir)
    res["emulator_sha"] = sha
    if sha is None:
        return done("BLOCKED", f"cannot determine emulator revision of {gpgx_dir} (git unavailable?)")
    if sha != lock.get("commit"):
        return done("BLOCKED", f"emulator checkout is {sha}, pin is {lock.get('commit')}; re-run fetch")

    with tempfile.TemporaryDirectory(prefix="gpgx-smoke-") as work:
        # Private copy: keeps saves out of the user's dir and stops the core auto-loading a
        # neighbouring .chd/.iso (which would switch it to Mode 1).
        rom_copy = os.path.join(work, "bios.bin")
        shutil.copyfile(rom, rom_copy)
        cmd = [sys.executable, "-I", HOST, core, rom_copy, str(frames), work, region]
        res["command"] = shlex.join(cmd)
        try:
            proc = run_host(cmd, timeout)
        except subprocess.TimeoutExpired:
            return done("FAIL", f"emulator host timed out after {timeout}s")
        res["trace"]["host_stderr_tail"] = (proc.stderr or "")[-2000:]
        if proc.returncode != 0:
            return done("FAIL", f"emulator host exited with code {proc.returncode}")
        try:
            obs = json.loads(proc.stdout)
        except ValueError:
            return done("FAIL", "emulator host produced no valid JSON")
        res["trace"].update(obs)
        if not obs.get("loaded"):
            return done("FAIL", "core rejected the ROM (retro_load_game returned false)")
        if "PRGRAM" not in obs.get("regions", []):
            return done("FAIL", "core did not enter Mega-CD mode (no PRG-RAM memory map published)")
        dumps = {}
        for space in SPACES:
            path = os.path.join(work, space + ".bin")
            if os.path.isfile(path):
                with open(path, "rb") as fh:
                    dumps[space] = fh.read()

    results = []
    for space, addr, want in checks:
        got = dumps.get(space, b"")[addr:addr + len(want)]
        results.append({"space": space, "offset": f"{addr:#x}", "expected": want.hex(), "actual": got.hex(),
                        "ok": got == want})
    res["trace"]["checks"] = results
    res["trace"]["stage"] = "BIOS-loaded"
    if not checks:
        return done("BLOCKED", "BIOS loaded and ran, but no --expect checkpoint was given; not judged")
    failed = [c for c in results if not c["ok"]]
    if failed:
        return done("FAIL", f"{len(failed)}/{len(results)} checkpoint assertion(s) did not hold")
    res["trace"]["stage"] = "Startup"
    return done("PASS", f"all {len(results)} checkpoint assertion(s) held after {frames} frames")


def fetch(cache=CACHE, lock=None, jobs=4):
    lock = lock or read_lock()
    git = ["git", "-C", cache]
    if not os.path.isdir(os.path.join(cache, ".git")):
        subprocess.run(["git", "init", "-q", cache], check=True)
        subprocess.run(git + ["remote", "add", "origin", lock["repo"]], check=True)
    subprocess.run(git + ["fetch", "-q", "--depth", "1", "origin", lock["commit"]], check=True)
    subprocess.run(git + ["checkout", "-q", "--detach", "-f", lock["commit"]], check=True)
    if git_head(cache) != lock["commit"]:
        sys.exit(f"checkout does not match pin {lock['commit']}")
    make = "mingw32-make" if sys.platform == "win32" and shutil.which("mingw32-make") else "make"
    subprocess.run([make, "-f", "Makefile.libretro", f"-j{jobs}"], cwd=cache, check=True)
    print(core_path(cache))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="clone/build the pinned core into the cache dir")
    f.add_argument("--cache", default=CACHE)
    m = sub.add_parser("make-fixture", help="write the synthetic fixture ROM")
    m.add_argument("out")
    r = sub.add_parser("run", help="boot a BIOS ROM headless and emit result JSON")
    r.add_argument("--rom", required=True)
    r.add_argument("--gpgx-dir", default=CACHE)
    r.add_argument("--frames", type=int, default=120)
    r.add_argument("--expect", action="append", default=[], help="SPACE:HEXADDR=HEXBYTES, SPACE=main|prg")
    r.add_argument("--region", default="auto", choices=["auto", "ntsc-u", "pal", "ntsc-j"])
    r.add_argument("--timeout", type=float, default=120)
    r.add_argument("--out", help="also write the result JSON here")
    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        return fetch(a.cache)
    if a.cmd == "make-fixture":
        with open(a.out, "wb") as fh:
            fh.write(make_fixture())
        return 0
    res = run(a.rom, a.gpgx_dir, a.frames, a.expect, a.region, a.timeout)
    text = json.dumps(res, indent=2)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return EXIT[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
