---
date: 2026-10-12
status: PASS-E2-L-cross-version-full-polymorphic-NewShape-command-to-CompItem
evidence: Real installed AE2025 + 2026 pinned BEE.dll machine instructions + MSVC RTTI/vtable + direct calls
---

# EXP-SHAPE-058 — Close the BEE_NewLayerTask<4> virtual dispatcher and native Comp owner gap

The previously missing F-VECTOR-056/057 link was an **internal polymorphic command task**, not a native direct call from the command table slot. Both pinned installed Adobe versions prove the full sequence:

`BEE_CmdNewVectorLayer` ID 101/106 → common Undo worker → BEE_DoCommand's 32-byte command table → +8 callback allocates a **0x30-byte** task, explicitly sets **kind 4** → type descriptor `.?AV?$BEE_NewLayerTask@$03@@` (native C++ template `BEE_NewLayerTask<4>`) and real MSVC vtable → virtual slot1 → stock native new layer worker → concrete `BEE_Layer::CreateLayerFromType` → CompItem attachment helper → `BEE_CompItem::AttachLayerToCompOnly`.

Actual worker-to-attach path:
- 2025 `0x3151D0 → 0x30B650 → 0x3920F0 → 0x392120`
- 2026 `0x31E800 → 0x314820 → 0x39D4A0 → 0x39D4D0`

Two independently compiled task callbacks (+8/+16) share the same RTTI-backed vtable. Slot2 refers to dvacore task serialization. Worker also references `TDB_StreamIDPath`, `BEE_CmdSeparateStreamDimensions` and positional/time/Undo logic. There is a branch for source 3D model that can select a different built-in layer kind; do not treat type4 as unconditional.

**PASS** `verify_bee_new_shape_complete_owner_chain.py` with installed binary SHA256 checks. Nothing was executed in the AE host. These discoveries reproduce native built-in Shape creation, **not** a valid third-party ABI or independently attached CNL layer. Native CNL Contents/Pen/BEE_VectorArt and safe owner-registration remain open. F-VECTOR-058 contains the exact references and limitations.
