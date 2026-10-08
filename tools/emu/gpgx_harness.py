"""Pinned Genesis Plus GX smoke-test harness (external, test-only; stdlib only).

  python -I tools/emu/gpgx_harness.py fetch                 # clone + build the pinned core
  python -I tools/emu/gpgx_harness.py version               # print built core revision (0 = at pin)
  python -I tools/emu/gpgx_harness.py make-fixture OUT.bin  # tiny synthetic test ROM
  python -I tools/emu/gpgx_harness.py run --rom BIOS.bin --expect main:FF0000=4F4B4F4B

`run` emits one evidence record (tools/evidence/result.schema.json, schema_version 1).
status: PASS | FAIL | SKIP (emulator not built) | BLOCKED (cannot judge).
checkpoint: 'startup' when --expect is given (PASS only if every assertion holds AND differs from
the power-on state), else 'bios-loaded' (PASS = core accepted and mapped the ROM in Mega-CD mode).
Exit code: PASS 0, FAIL 1, SKIP 3, BLOCKED 4.

The emulator lives outside the repository: $GPGX_CACHE_DIR, default <user cache dir>/oss-mcd-bios/gpgx.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(HERE, "gpgx.lock")
HOST = os.path.join(HERE, "libretro_host.py")
EXIT = {"PASS": 0, "FAIL": 1, "SKIP": 3, "BLOCKED": 4}
SPACES = {"main": (0xFF0000, 0x10000), "prg": (0x000000, 0x80000)}  # 68K address base, size
BOOTROM_SIZE = 0x20000
LOG_MAX_LINES, LOG_MAX_CHARS = 40, 4096
_PATHS = re.compile(r"\b[A-Za-z]:[\\/][^\s'\"]*|(?<![\w.:/])/(?:home|Users|root|tmp|var|opt|mnt|private)(?:/[^\s'\"]*)?")


def cache_dir():
    if os.environ.get("GPGX_CACHE_DIR"):
        return os.environ["GPGX_CACHE_DIR"]
    base = (os.environ.get("LOCALAPPDATA") if sys.platform == "win32" else os.environ.get("XDG_CACHE_HOME"))
    return os.path.join(base or os.path.join(os.path.expanduser("~"), ".cache"), "oss-mcd-bios", "gpgx")


def read_lock(path=None):
    with open(path or LOCK, encoding="utf-8") as fh:
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


def check_rom(data, mode):
    """Loader preconditions of the pinned core (docs/emulator/gpgx-investigation.md). -> (blockers, warnings)"""
    blockers, warnings = [], []
    if not data:
        return ["ROM is empty"], warnings
    if len(data) != BOOTROM_SIZE:
        warnings.append(f"ROM size {len(data):#x} != {BOOTROM_SIZE:#x}; core uses exactly the first 128KB")
    if mode == "system":
        return blockers, warnings  # ROM used unchanged as the system-directory BIOS file
    # mode 'bootrom': ROM loaded as content -- these are emulator-loader demands, not BIOS requirements
    if len(data) > 0x800000:
        blockers.append("ROM larger than 8MB; core only treats <=8MB images as BOOT ROM")
    if data[0x180:0x182] != b"BR":
        blockers.append("bootrom mode: header $180 is not 'BR'; core would not map the image as CD BOOT ROM")
    if b"C" in data[0x190:0x19E]:
        blockers.append("bootrom mode: I/O support $190 contains 'C'; core would boot it as a Mode 1 cartridge")
    if b"FLUX" in data[0x120:0x150]:
        blockers.append("bootrom mode: domestic name contains 'FLUX'; core would boot it as a Mode 1 cartridge")
    if b"SEGA PICO" in data[0x100:0x110]:
        blockers.append("bootrom mode: console name contains 'SEGA PICO'; core would select Pico hardware")
    if data[0x100:0x104] != b"SEGA" and len(data) % 512 == 0 and (len(data) // 512) % 2:
        blockers.append("bootrom mode: core would strip a 512-byte copier header")
    return blockers, warnings


def parse_expect(text):
    """'main:FF0000=4F4B' -> ('main', 0x0, b'OK'). Addresses are 68K addresses; out of range is an error."""
    loc, value = text.split("=", 1)
    space, addr = loc.split(":", 1)
    if space not in SPACES:
        raise ValueError(f"unknown space {space!r} in {text!r} (use main or prg)")
    want = bytes.fromhex(value)
    if not want:
        raise ValueError(f"empty expected value in {text!r}")
    base, size = SPACES[space]
    offset = int(addr, 16) - base
    if offset < 0 or offset + len(want) > size:
        raise ValueError(f"{text!r} outside {space} ${base:06X}-${base + size - 1:06X}")
    return space, offset, want


def make_fixture():
    """128KB synthetic ROM, hand-assembled here: writes 'OKOK' to $FF0000 then loops forever."""
    rom = bytearray(BOOTROM_SIZE)
    rom[0:8] = bytes.fromhex("00FFFE00 00000200")             # reset SSP, reset PC
    rom[8:0x100] = bytes.fromhex("0000020A") * 62             # other vectors -> idle loop
    rom[0x100:0x200] = b" " * 0x100
    rom[0x100:0x110] = b"SEGA MEGA DRIVE "
    rom[0x120:0x13C] = b"OSS-MCD-BIOS HARNESS FIXTURE"
    rom[0x180:0x182] = b"BR"  # only needed for --mode bootrom
    rom[0x190] = ord("J")
    rom[0x1F0] = ord("U")
    rom[0x200:0x20C] = bytes.fromhex("23FC 4F4B4F4B 00FF0000"   # move.l #'OKOK',($FF0000).l
                                     "60FE")                   # bra.s *
    return bytes(rom)


def blank_disc():
    """Synthetic, data-less cooked disc image: only the 'SEGADISCSYSTEM' ID the core probes for
    (cdd.c cdd_load) so it enters Mega-CD mode and loads the BIOS from the system directory."""
    disc = bytearray(16 * 2048)
    disc[0:16] = b"SEGADISCSYSTEM  "
    return bytes(disc)


def sanitize(text):
    text = _PATHS.sub("<path>", text.replace("\r\n", "\n"))
    return "\n".join(text.strip("\n").split("\n")[-LOG_MAX_LINES:])[-LOG_MAX_CHARS:]


def run_host(cmd, timeout):
    """The executable boundary (mocked in unit tests)."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def run(rom, gpgx_dir=None, frames=120, expects=(), region="auto", timeout=120, lock=None,
        mode="system", rom_commit=None):
    gpgx_dir = gpgx_dir or cache_dir()
    observed = {"load_mode": mode, "region": region, "frames_requested": frames}
    rec = {"schema_version": 1, "status": "BLOCKED", "checkpoint": "startup" if expects else "bios-loaded",
           "rom_sha256": None, "rom_commit": rom_commit,
           "emulator": {"id": "gpgx", "version": None, "sha": None},
           "environment": {"os": platform.system().lower() or "unknown",
                           "arch": platform.machine().lower() or "unknown", "python": platform.python_version()},
           "observed": observed, "log_excerpt": "", "reason": None}

    def done(status, reason):
        rec.update(status=status, reason=reason)
        return rec

    if lock is None:
        try:
            lock = read_lock()
        except OSError as e:
            return done("BLOCKED", f"lock file not readable: {e}")
    if not re.fullmatch(r"[0-9a-f]{40}", lock.get("commit", "")):
        return done("BLOCKED", "lock file has no valid 'commit=' pin")
    rec["emulator"]["version"] = lock.get("version")
    observed["pinned_sha"] = lock["commit"]
    if rom_commit is not None and not re.fullmatch(r"[0-9a-f]{7,40}", rom_commit):
        return done("BLOCKED", f"bad --rom-commit {rom_commit!r}")
    try:
        with open(rom, "rb") as fh:
            data = fh.read()
    except OSError as e:
        return done("BLOCKED", f"BIOS ROM not readable: {e.strerror}")
    rec["rom_sha256"] = hashlib.sha256(data).hexdigest()
    blockers, observed["rom_warnings"] = check_rom(data, mode)
    if blockers:
        return done("BLOCKED", "; ".join(blockers))
    try:
        checks = [parse_expect(e) for e in expects]
    except ValueError as e:
        return done("BLOCKED", f"bad --expect: {e}")

    core = core_path(gpgx_dir)
    if not os.path.isfile(core):
        return done("SKIP", "emulator core not built; run: python -I tools/emu/gpgx_harness.py fetch")
    sha = git_head(gpgx_dir)
    rec["emulator"]["sha"] = sha if sha and re.fullmatch(r"[0-9a-f]{7,64}", sha) else None
    if sha is None:
        return done("BLOCKED", "cannot determine emulator revision of the cache checkout (git unavailable?)")
    if sha != lock["commit"]:
        return done("BLOCKED", f"emulator checkout is {sha}, pin is {lock['commit']}; re-run fetch")

    with tempfile.TemporaryDirectory(prefix="gpgx-smoke-") as work:
        # Private dir: keeps saves out of the user's dir and stops the core auto-loading a
        # neighbouring .chd/.iso. The ROM bytes are used unchanged in both modes.
        if mode == "system":
            os.makedirs(os.path.join(work, "system"))
            for suffix in "UEJ":  # same file under every region name: region only picks the filename
                shutil.copyfile(rom, os.path.join(work, "system", f"bios_CD_{suffix}.bin"))
            content = os.path.join(work, "disc.iso")
            with open(content, "wb") as fh:
                fh.write(blank_disc())
        else:
            content = os.path.join(work, "bios.bin")
            shutil.copyfile(rom, content)
        cmd = [sys.executable, "-I", HOST, core, content, str(frames), work, region]
        observed["command"] = (f"python -I tools/emu/libretro_host.py <core> <{os.path.basename(content)}> "
                               f"{frames} <workdir> {region}")
        try:
            proc = run_host(cmd, timeout)
        except subprocess.TimeoutExpired:
            return done("FAIL", f"emulator host timed out after {timeout}s")
        stderr = proc.stderr or ""
        rec["log_excerpt"] = sanitize(stderr)
        if proc.returncode != 0:
            return done("FAIL", f"emulator host exited with code {proc.returncode}")
        try:
            obs = json.loads(proc.stdout)
        except ValueError:
            return done("FAIL", "emulator host produced no valid JSON")
        rec["log_excerpt"] = sanitize("\n".join(obs.pop("core_log", [])) + "\n" + stderr)
        observed.update(obs)
        if not obs.get("loaded"):
            return done("FAIL", "core rejected the content (retro_load_game returned false)")
        if "PRGRAM" not in obs.get("regions", []):
            return done("FAIL", "core did not enter Mega-CD mode (no PRG-RAM memory map published)")
        dumps = {}
        for space in SPACES:
            for suffix in (".init.bin", ".bin"):
                path = os.path.join(work, space + suffix)
                if os.path.isfile(path):
                    with open(path, "rb") as fh:
                        dumps[space + suffix] = fh.read()

    results = []
    for space, offset, want in checks:
        got = dumps.get(space + ".bin", b"")[offset:offset + len(want)]
        init = dumps.get(space + ".init.bin", b"")[offset:offset + len(want)]
        results.append({"space": space, "addr": f"{SPACES[space][0] + offset:06X}", "expected": want.hex(),
                        "actual": got.hex(), "power_on": init.hex(),
                        "ok": got == want and len(init) == len(want) and init != want})
    observed["checks"] = results
    if not checks:
        return done("PASS", f"core accepted and mapped the BIOS in Mega-CD mode ({mode} mode) and ran "
                            f"{frames} frames; no checkpoint asserted, so this says nothing about startup")
    failed = [c for c in results if not c["ok"]]
    if failed:
        same = [c for c in failed if c["power_on"] == c["expected"]]
        why = f"; {len(same)} expected value(s) equal the power-on state, so they prove nothing" if same else ""
        return done("FAIL", f"{len(failed)}/{len(results)} checkpoint assertion(s) did not hold{why}")
    return done("PASS", f"all {len(results)} checkpoint assertion(s) held after {frames} frames "
                        "and differ from the power-on state")


def fetch(cache=None, lock=None, jobs=4):
    cache = cache or cache_dir()
    lock = lock or read_lock()
    git = ["git", "-C", cache]
    if not os.path.isdir(os.path.join(cache, ".git")):
        os.makedirs(cache, exist_ok=True)
        subprocess.run(["git", "init", "-q", cache], check=True)
        subprocess.run(git + ["remote", "add", "origin", lock["url"]], check=True)
    subprocess.run(git + ["fetch", "-q", "--depth", "1", "origin", lock["commit"]], check=True)
    subprocess.run(git + ["checkout", "-q", "--detach", "-f", lock["commit"]], check=True)
    if git_head(cache) != lock["commit"]:
        sys.exit(f"checkout does not match pin {lock['commit']}")
    make = "mingw32-make" if sys.platform == "win32" and shutil.which("mingw32-make") else "make"
    subprocess.run([make, "-f", "Makefile.libretro", f"-j{jobs}"], cwd=cache, check=True)
    print(core_path(cache))
    return 0


def version(cache=None):
    """Print the built core's revision. 0 = at the pin, 1 = other revision, 3 = not built."""
    cache = cache or cache_dir()
    if not os.path.isfile(core_path(cache)):
        print("gpgx not built")
        return 3
    sha = git_head(cache)
    print(f"gpgx {sha}")
    return 0 if sha == read_lock().get("commit") else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="clone/build the pinned core into the cache dir")
    f.add_argument("--cache")
    v = sub.add_parser("version", help="print the built core revision")
    v.add_argument("--cache")
    m = sub.add_parser("make-fixture", help="write the synthetic fixture ROM")
    m.add_argument("out")
    r = sub.add_parser("run", help="boot a BIOS ROM headless and emit an evidence record")
    r.add_argument("--rom", required=True)
    r.add_argument("--mode", default="system", choices=["system", "bootrom"],
                   help="system: ROM as bios_CD_*.bin + blank synthetic disc (default, no header demands); "
                        "bootrom: ROM loaded as content, needs 'BR' at $180 (emulator-specific)")
    r.add_argument("--gpgx-dir", help="default: $GPGX_CACHE_DIR or <user cache>/oss-mcd-bios/gpgx")
    r.add_argument("--frames", type=int, default=120)
    r.add_argument("--expect", action="append", default=[], help="SPACE:HEXADDR=HEXBYTES; main $FF0000-$FFFFFF, "
                                                                  "prg $000000-$07FFFF")
    r.add_argument("--region", default="auto", choices=["auto", "ntsc-u", "pal", "ntsc-j"])
    r.add_argument("--rom-commit", help="git commit the ROM was built from")
    r.add_argument("--timeout", type=float, default=120)
    r.add_argument("--out", help="also write the record here")
    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        return fetch(a.cache)
    if a.cmd == "version":
        return version(a.cache)
    if a.cmd == "make-fixture":
        with open(a.out, "wb") as fh:
            fh.write(make_fixture())
        return 0
    rec = run(a.rom, a.gpgx_dir, a.frames, a.expect, a.region, a.timeout, mode=a.mode, rom_commit=a.rom_commit)
    text = json.dumps(rec, indent=2)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return EXIT[rec["status"]]


if __name__ == "__main__":
    sys.exit(main())
