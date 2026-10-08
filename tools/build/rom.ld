/* oss-mcd-bios linker script (MIT).
 * UNVERIFIED: link address 0 assumes the image is seen by the CPU at address 0.
 * The image size limit is enforced by tools/rom/mkrom.py from tools/rom/rom-config.json. */
OUTPUT_ARCH(m68k)
ENTRY(reset)

SECTIONS
{
    .vectors 0 : { KEEP(*(.vectors)) }
    .text : { *(.text .text.*) *(.rodata .rodata.*) }
    /DISCARD/ : { *(.data .data.* .bss .bss.* .comment .note.*) }
}
