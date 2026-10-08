| oss-mcd-bios: minimal original 68000 reset skeleton (MIT, see LICENSE).
| Assembled with GNU as (m68k-elf), MIT/Motorola mixed syntax, '|' comments.
|
| This is a toolchain smoke target, NOT a working BIOS. It is not claimed to
| boot on any emulator or hardware. It only shows that the pinned toolchain
| produces a deterministic image with a 68000 exception vector table.
|
| UNVERIFIED: where this image is mapped in the Mega-CD address space, and
| therefore whether vector 0/1 below are what the CPU fetches at reset.
| The ROM-layout specification (Issue #1) must confirm this.

        .equ    INITIAL_SSP, 0x00FFFE00     | UNVERIFIED placeholder stack top

        .section .vectors, "a"
        .long   INITIAL_SSP                 | vector 0: initial SSP
        .long   reset                       | vector 1: initial PC
        .rept   62                          | vectors 2-63
        .long   unhandled
        .endr

        .text
        .globl  reset
reset:
        move.w  #0x2700, %sr                | supervisor mode, mask all interrupts
1:      stop    #0x2700
        bra.s   1b

unhandled:
        stop    #0x2700
        bra.s   unhandled
