"""Pad a raw objcopy image to the configured ROM size and print its SHA-256.

Usage: python3 -I tools/rom/mkrom.py RAW CONFIG OUT
Writes OUT and OUT.sha256 (sha256sum format). No timestamps or host data are embedded.
"""
import hashlib
import json
import os
import sys


def main(raw_path, config_path, out_path):
    with open(config_path) as f:
        config = json.load(f)
    size, fill = config["rom_size"], config["fill_byte"]
    with open(raw_path, "rb") as f:
        raw = f.read()
    if len(raw) > size:
        sys.exit(f"mkrom: image is {len(raw)} bytes, exceeds rom_size {size}")
    rom = raw + bytes([fill]) * (size - len(raw))
    with open(out_path, "wb") as f:
        f.write(rom)
    digest = hashlib.sha256(rom).hexdigest()
    with open(out_path + ".sha256", "w", newline="\n") as f:
        f.write(f"{digest}  {os.path.basename(out_path)}\n")
    print(f"{digest}  {out_path} ({len(raw)} bytes code, {size} bytes total)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
