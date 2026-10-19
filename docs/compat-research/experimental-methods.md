# Seven complementary methods to recover missing behavior

## M1: Public documentation and independently authored SDKs

Consult CPU vendor manuals, authorized public technical descriptions and independently written SDK headers/wrappers. Collect function names, input/output candidates and error cases, with exact source URL, revision, line/page and permissions. A public GitHub repository can contain knowledge originating in disassembly: permissive code licensing does not automatically clear provenance.

## M2: Multiple emulator implementations

Compare Genesis Plus GX (upstream and own fork), PicoDrive and other confirmed Mega-CD-capable emulators. Observe Main/Sub CPU, Word RAM, CD controller, DMA, IRQ and audio with identical **synthetic** stimuli. Record emulator revision and shared ancestry. Agreement on a result is supporting evidence, not conclusive proof of real hardware behavior. Treat disagreements as open questions.

## M3: Existing BIOS HLE

ClownMDEmu's [HLE explainer](https://clownacy.wordpress.com/2023/10/13/clownmdemu-high-level-emulation/) describes emulator-side replacement for BIOS startup and service calls. The [Snatcher host-side HLE report](snatcher-hle-case-study.md) offers another concrete example. Neither proves a guest 68000 ROM will operate on hardware.

Keep three models distinct: emulator HLE (native host API replacement), hybrid stub+HLE, and stand-alone 68000 BIOS ROM. The published ClownMDEmu development accounts describe reference disassembly in parts of their history; until Issue #17 is resolved, use those materials only for general research questions, not implementation tables or code.

## M4: Black-box reference probing

If access and use are permitted, run independently authored small programs against a legitimately acquired reference BIOS on emulator or real hardware. Vary one argument at a time; record registers, flags, memory deltas, event order, timeouts, errors and reset/retry. Keep proprietary reference ROMs and extracts out of Git and CI. A black-box observation still needs attribution and review of its lawful use.

## M5: Game-side required behavior

For legitimately testable retail game editions, trace guest API calls and later use of results in debugger instrumentation where lawful. Look for return register checks, shared RAM reads, polling, callbacks, timing and fallback paths. Publish **behavior requirements and hashes**, not copied program disassembly/code, game assets or disc sectors. A single observed branch cannot prove all game paths.

## M6: Independently authored CD/hardware probes

Generate shareable m68k program source and disc images with original content, measure Main/Sub communication, DMA, sector transfer, memory ownership, IRQ, PCM and reset; cross-check independent emulators and hardware when safe. The probe itself may be defective, so build sanity checks against proven CPU semantics.

## M7: Differential, metamorphic and stateful fuzz tests

Use controlled inputs to compare outputs and normalized event ordering. Metamorphic tests change inputs expected to be irrelevant or predictably transformed. Stateful fuzzing explores repeated calls, interleaved interrupts, no disc, invalid parameters, failed transfers, ownership changes and save errors. Reduce every mismatch to the **first divergence** and retain an independently distributable reproducer.

## Workflow for an individual unknown

1. State a single observable question.
2. Review source permission, lineage, and currently supported facts.
3. List competing behavior hypotheses.
4. Write the smallest discriminating fixture.
5. Run it in permitted environments and record versions, hashes, events, and uncertainties.
6. Independently review observations and write a behavioral contract.
7. Implement any algorithm that meets the **externally visible** contract.
8. Validate with synthetic and legal commercial-game scenarios, keep regression tests.
9. Reopen the contract when another title contradicts it.

A skipped, blocked, or mocked emulator run is not an emulator-core success.
