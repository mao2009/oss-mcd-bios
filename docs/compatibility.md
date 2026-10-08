# Compatibility and testing

All compatibility claims require a recorded environment, ROM hash, emulator/core version and reproducible observation.

## Test stages

| Stage | Meaning |
| --- | --- |
| ROM-built | An image is generated and satisfies structural checks |
| BIOS-loaded | The emulator accepts and maps the image |
| Startup | Reset/initialization reaches the expected checkpoint |
| Disc-detected | Disc presence and metadata are read |
| Homebrew-boot | Independently authored test disc starts |
| Game-boot | A specified commercial title reaches executable game code |
| Playable | Defined gameplay scenario can be played |
| Completion-tested | A title was played through to an agreed endpoint |

Passing one stage **does not imply** passing the next.

## Initial targets

- Genesis Plus GX: primary software emulator target (version/core to be pinned).
- PicoDrive: independent emulator cross-check.
- FPGA and real hardware: later validation, without emulator-only dependencies.

## Test report template

- ROM commit and SHA-256:
- Target emulator and exact version/core:
- Host platform:
- Region/model and memory configuration:
- Disc/test image provenance:
- Stage reached:
- Observed trace / screenshot / assertion:
- Known limitations:
- Reproduction steps:

No commercial game content or proprietary BIOS files should enter this repository, CI artifacts or test fixtures.
