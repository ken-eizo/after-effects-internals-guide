# EXP-SHAPE-081 — Real Adobe Paint.aex to host Paint Suite function table (2025/2026)

Scope: Brush-tool-generated **Paint** effect; exclude Paint Bucket and Brush Strokes.

## Goal
Distinguish ordinary AEX effect plugin interface from the actual Adobe-private Paint evaluator and Timeline-native backing registration. Demonstrate the host's named `Paint Suite` bridge with static disassembly of original installed binaries.

## Method
- SHA-pinned AfterFXLib.dll and Required/Paint.aex.
- Enumerate full host exports with dumpbin; find `PaintEffectEntryPoint`.
- Locate exact host `Paint Suite\0` literal and verify RIP-relative LEA instruction to it in host's .text.
- Resolve nearby RIP-relative LEA to dispatch-table data whose **first 64-bit pointer** equals loaded-base + PaintEffectEntryPoint RVA.
- Verify nearby host registration function call instruction.
- Verify both AEX `EffectMainExtra` exports delegate to the same function that references `Paint Suite`.
- Independently ensure PaintBucket.aex is a distinct binary with no matching private Suite marker.

## Acceptance
```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_paint_suite_host_bridge.py"
```

Result: **PASS both AE2025 and AE2026**, the host suite table's first function pointer is the exported `PaintEffectEntryPoint`. This is not evidence of third-party arbitrary TDB stream registration. No private API executed; installed binaries not modified.

Record: `research/findings/F-VECTOR-081-paint-suite-host-owned-effect-bridge.md`.
Data: `datasets/ae-paint-suite-host-bridge-2025-2026.json`.
