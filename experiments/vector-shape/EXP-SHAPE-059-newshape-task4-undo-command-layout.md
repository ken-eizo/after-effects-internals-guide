---
date: 2026-10-12
status: PASS-e2-l-real-BEE2025-2026-command-object-layout
evidence: on-disk real x64 constructors + RTTI and virtual serialization
---

# EXP-SHAPE-059 — Resolve native BEE_NewLayerTask<4> memory layout and task Undo serializer

After recovering the full native New Shape command graph (EXP-SHAPE-058), the constructor implementations at `0x5443E0` (AE2025) and `0x563200` (AE2026) were disassembled. Both copy 32 bytes of context to `this+0x08` and store constructor input layer kind **4** at `this+0x28`, with a native RTTI-backed vtable at `this+0x00`. Allocation is exactly 0x30 bytes. Virtual slot1 reads this `+0x28` kind and passes it into real `BEE_Layer::CreateLayerFromType`. An alternate constructor restores that kind from command data; virtual slot2 imports `dvacore::serialization::AddToObject` at least five times. `verify_bee_newshape_task4_layout_undo_serializer.py` independently verified both installed versions **PASS**.

This shows the actual host Undo command *state object* for a stock Shape Layer is native polymorphic and serializable; it does **not** prove a foreign CNL Undo command may be registered, or that any external CNL owner works. No private functions called in AE, no GUI interaction, no AE binary patch, no CompNodeAE change, Phase F untouched.

See F-VECTOR-059.
