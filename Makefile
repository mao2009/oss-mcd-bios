# oss-mcd-bios build. Single command: `make`
# (fetches + SHA-256-verifies + builds pinned binutils on first run, then assembles,
#  links, pads, prints the ROM SHA-256 and runs the structural validator).
# Other targets: `make test` (validator unit tests), `make clean`.
# Requires: bash, curl, xz, tar, sha256sum, a host C compiler, make, python3.

TC     ?= build/toolchain
CROSS   = $(TC)/bin/m68k-elf-
PYTHON ?= python3
ROM     = build/oss-mcd-bios.bin

.PHONY: all toolchain validate test clean
.DELETE_ON_ERROR:

all: validate

# Phony + order-only: the script itself is a no-op when the pinned version is installed.
toolchain:
	bash tools/build/toolchain.sh $(TC)

build/boot.o: src/boot/boot.s | toolchain
	@mkdir -p build
	$(CROSS)as -m68000 -o $@ $<

build/rom.elf: build/boot.o tools/build/rom.ld
	$(CROSS)ld -T tools/build/rom.ld -o $@ build/boot.o

build/rom.raw: build/rom.elf
	$(CROSS)objcopy -O binary $< $@

$(ROM): build/rom.raw tools/rom/rom-config.json tools/rom/mkrom.py
	$(PYTHON) -I tools/rom/mkrom.py build/rom.raw tools/rom/rom-config.json $@

validate: $(ROM)
	$(PYTHON) -I tools/rom/validate.py $(ROM)

test:
	$(PYTHON) -I -B -m unittest discover -s tools/rom -p "test_*.py" -v

clean:
	rm -f build/boot.o build/rom.elf build/rom.raw $(ROM) $(ROM).sha256
