---
date: 2026-10-14
status: PASS 2/2 AE2025/2026 read-only actual installed binary Paint Suite bridge
evidence: E2-L pinned AEX and AfterFXLib SHA; PE RDATA registration dispatch, direct LEA RIP references, native PaintEffectEntryPoint exports
---
# F-VECTOR-081 — Brush-created Paint effect AEX delegates through host-owned Paint Suite

## Precise scope — NOT Paint Bucket / Brush Strokes

This is the special **Paint effect created when using After Effects' brush tool**, with a nested Strokes and Brush group in AE's ordinary Timeline. It is not `Plug-ins/Effects/PaintBucket.aex`, and not `Plug-ins/Effects/Brush_Strokes.aex`. Both are distinct effects and must be excluded from this research.

`Required/Paint.aex` exists in the installed AE2025 and AE2026 releases and exports `EffectMainExtra`, `EffectMainExtra2` and `PluginDataEntryFunction`. It does not directly import `BEE.dll` or `TDB.dll`. Do not interpret this as its implementing Adobe native Strokes hierarchy by itself.

## Positive static disassembly: Paint.aex -> Paint Suite -> AfterFXLib host

`Paint.aex`'s two `EffectMainExtra` entrypoints feed a **single internal callback** that references the exact suite string `Paint Suite`. The host `AfterFXLib.dll` registers that suite string alongside a native function-pointer table whose **first element** is `PaintEffectEntryPoint`. This is the actual host Paint effect entrypoint exported by `AfterFXLib.dll`. The observed registration machine instructions use a RIP-relative LEA of the suite literal and of the dispatch table, followed by a call through a host function pointer.

| Evidence | AE2025 | AE2026 |
| --- | --- | --- |
| `Paint.aex` direct use of `Paint Suite` | RVA `0x1424` | RVA `0x1427` |
| `AfterFXLib.dll` host suite register routine | RVA `0x924640` | RVA `0xA296B0` |
| `Paint Suite` literal LEA | RVA `0x92495F` | RVA `0xA299CF` |
| Host function table RVA | `0x1F7EC68` | `0x22EDD78` |
| Table first entry `PaintEffectEntryPoint` RVA | `0x973B90` | `0xA79050` |
| Host suite registration call instruction | `0x92496A` | `0xA299DA` |

Exact SHA256:
- AE2025 `AfterFXLib.dll`: `3911deb498964fc82a2930fbdc9361f7977d804fca47d15538755b6558f7a836`
- AE2026 `AfterFXLib.dll`: `c8d8a8697be7597cf4c59bb7ad6bac4a065d15f2ede4528c371c859c64af0964`
- AE2025 `Paint.aex`: `50ddd78f6e7d5352ed4e156267d971f70a32e44bb62b02956f2916ce5272aef4`
- AE2026 `Paint.aex`: `b1190b667f27521540f640bf18f81468b7549a660115209b5312e791087fa62e`

Machine verifier: `experiments/vector-shape/probe-src/tools/verify_paint_suite_host_bridge.py`.
Dataset: `datasets/ae-paint-suite-host-bridge-2025-2026.json`.

In the same host, `CComposition::DoPaintCommand` and `GetPaintGroupStream` exist as native exports, consistent with brush-specific editor/paint handling. This finding does not claim those methods' full command-to-effect-creation call chain has yet been proved.

## How this relates to Paint's authentic native Timeline

F-VECTOR-080 independently proved all five major `BEE_Paint*::Create` functions (PaintAtom, PaintStrokesGroup, PaintEffect, PaintProperties, PaintTransform) are passed with typed MatchNames to **`TDB_ScRegisterStreams::Register`** during `BEE_AVLayer::RegisterStreams` (AE2025 and AE2026). Therefore the host **pre-registers** the Paint Stream hierarchy, whereas `Paint.aex` delegates effect calls into a host-provided `Paint Suite`.

BEE has exact native match strings `ADBE Paint`, `ADBE Paint Group`, `ADBE Paint Atom`, `ADBE Paint Shape`, `ADBE Paint Properties`, `ADBE Paint Transform`, `ADBE Paint Position`, `ADBE Paint Opacity`, etc. These are host-owned native Stream definitions.

## Public SDK vs internal provider

The public Adobe SDK 25.6 example `Examples/AEGP/Streamie/Streamie.cpp` explicitly inspects an existing Paint effect and its `ADBE Paint Group`, and uses **public AEGP** `AEGP_ReorderStream`, `AEGP_SetStreamName`, `AEGP_DuplicateStream`, `AEGP_DeleteStream` on preexisting Paint strokes. This **positively demonstrates third-party manipulation of already registered native Paint child Streams**; it does **not** contain any foreign `TDB_StreamBase` class registrar, custom PaintAtom factory, or stream parent provider.

The Paint-specific suite name `Paint Suite` does not appear in the 70 inspected installed public SDK 25.6 header files. This is a scoped observation, not a universal absence proof for all Adobe APIs.

## Actual frontier

A third-party native custom group inside ordinary AE Timeline needs a safe, host-accepted foreign `TDB_StreamBase` creator registration + owner lifecycle + persistence/undo/UI capability. Merely loading `Paint.aex` from `Required` or building another PF Effect does not grant this privilege. `TDB_ScRegisterStreams::Register` is exported but uses private C++ ABI, `std::function`, and versioned host factory/lifetime rules. An offline PE trace is NOT permission to execute it inside the production Adobe host.

No Adobe product files changed, no private API executed, no Paint Bucket confusion, no new custom stream attached; status of foreign native registration remains **NOT DEMONSTRATED**.
