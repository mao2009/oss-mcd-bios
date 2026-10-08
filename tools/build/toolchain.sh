#!/usr/bin/env bash
# Fetch, verify (SHA-256) and build the pinned GNU binutils m68k-elf toolchain.
# Only gas (as), ld and objcopy are used. See docs/toolchain.md and docs/adr/0001-toolchain.md.
# The pin (version, URL, SHA-256, target) is read from tools/build/toolchain.lock only.
#
# Usage: tools/build/toolchain.sh [PREFIX]   (default PREFIX: build/toolchain)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
lock() { sed -n "s/^$1=//p" "$ROOT/tools/build/toolchain.lock" | tr -d '\r'; }
[ "$(lock name)" = binutils ] || { echo "toolchain.lock: name must be binutils" >&2; exit 1; }
BINUTILS_VERSION="$(lock version)"; : "${BINUTILS_VERSION:?missing version in toolchain.lock}"
BINUTILS_SHA256="$(lock sha256)";   : "${BINUTILS_SHA256:?missing sha256 in toolchain.lock}"
BINUTILS_URL="$(lock url)";         : "${BINUTILS_URL:?missing url in toolchain.lock}"
TARGET="$(lock target)";            : "${TARGET:?missing target in toolchain.lock}"

PREFIX="$(mkdir -p "${1:-$ROOT/build/toolchain}" && cd "${1:-$ROOT/build/toolchain}" && pwd)"
WORK="${TOOLCHAIN_WORK:-$ROOT/build/toolchain-src}"
STAMP="$PREFIX/.binutils-${BINUTILS_VERSION}-${BINUTILS_SHA256}"

if [ -f "$STAMP" ] && [ -x "$PREFIX/bin/$TARGET-as" ]; then
  echo "toolchain: binutils $BINUTILS_VERSION ($TARGET) already installed in $PREFIX"
  exit 0
fi

mkdir -p "$WORK"
TARBALL="$WORK/binutils-${BINUTILS_VERSION}.tar.xz"
[ -f "$TARBALL" ] || curl -fL --retry 3 -o "$TARBALL" "$BINUTILS_URL"
echo "$BINUTILS_SHA256  $TARBALL" | sha256sum -c - || { rm -f "$TARBALL"; echo "SHA-256 mismatch" >&2; exit 1; }

rm -rf "$WORK/src" "$WORK/obj"
mkdir -p "$WORK/src" "$WORK/obj"
tar -xJf "$TARBALL" -C "$WORK/src" --strip-components=1
cd "$WORK/obj"
"$WORK/src/configure" --target="$TARGET" --prefix="$PREFIX" \
  --disable-nls --disable-werror --disable-multilib --disable-gdb --disable-gdbserver \
  --disable-sim --disable-gprofng --disable-readline --disable-libdecnumber --without-zstd
# -j2 keeps peak memory low on small machines/runners. MAKEINFO=true: docs are not
# needed and texinfo is not installed on stock CI runners.
make -j"${JOBS:-2}" MAKEINFO=true all-gas all-ld all-binutils
make MAKEINFO=true install-gas install-ld install-binutils
"$PREFIX/bin/$TARGET-as" --version | head -1 | grep -F " $BINUTILS_VERSION" \
  || { echo "installed as does not report version $BINUTILS_VERSION" >&2; exit 1; }
touch "$STAMP"
