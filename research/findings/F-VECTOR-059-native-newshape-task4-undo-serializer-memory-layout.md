---
date: 2026-10-12
status: PASS-native-BEE-NewLayerTask4-memory-layout-and-Undo-serialization-2025-2026
evidence: E2-L actual installed BEE.dll constructor and virtual method machine code
---

# F-VECTOR-059 — BEE_NewLayerTask<4>: 48-byte task object ABI, layer-kind field, state serialization

F-VECTOR-058 recovered a complete built-in native `New Shape Layer` command-to-comp ownership connection. This finding establishes the **concrete native command object structure** through cross-version static x64 code and explains why wrapping a custom TDB creator in a generic Undo call is insufficient to create a real layer.

## ABI-level typed task (both pinned AE versions)

The table record's +8 callback allocates `0x30` bytes, supplies **`mov r8d,4`** and constructs an RTTI-backed `BEE_NewLayerTask<4>`. The constructor:

- Installs a native vtable at `[this+0]`, using MSVC `RTTI TypeDescriptor .?AV?$BEE_NewLayerTask@$03@@`.
- Copies 32 bytes of the command context into `[this+8]` using an optimized 256-bit move, indicating a by-value context payload at offsets `+0x08..+0x27`.
- Stores a copy of the constructor argument `R8D` at `[this+0x28]`: **layer kind 4** for the New Shape Layer task.
- The virtual slot1 execution code later performs **`mov ecx, dword ptr [rbx+0x28]`** and passes that stored kind toward the stock `CreateLayerFromType` path. Its type choice can be overridden by the native conditional special case for 3D model inputs.

The alternate +16 callback also constructs the **same RTTI-backed class**, using a separate initialization path that reads an input command payload and restores `[this+0x28]` and other fields. The class's virtual slot2 contains **at least five** direct imported `dvacore::serialization::AddToObject` callsites, with additional virtual calls. This is concrete evidence for a serialized command state; full per-field semantics and actual foreign-CNL Undo replay contract have not been verified.

| Measured memory offset | Native observation | Significance |
| --- | --- | --- |
| +0x00 | vtable pointer | polymorphic BEE task object, host code owns compiled vtable |
| +0x08 .. +0x27 | 32-byte state copy | serialized/Undo-context payload, lifetime is native |
| +0x28 (4 bytes) | layer kind value 4 | consumed by the actual native creation worker |
| total allocation | 0x30 bytes | actual BEE command task size on 2025 and 2026 |

The matching +8 constructor implementation:
- AE2025 `0x5443E0`, copy at `0x544414`, kind write at `0x544419`.
- AE2026 `0x563200`, copy at `0x563234`, kind write at `0x563239`.

**Important:** this is a reverse-engineered **built-in command object layout**, not a stable or authorized Adobe third-party plugin ABI. Copying 48 bytes into an AEX-defined object or changing the built-in command's stored type to an unknown integer cannot overcome the fixed native layer-kind dispatcher or establish a new native owner.

## Reproduction

- `experiments/vector-shape/probe-src/tools/audit_bee_newshape_task4_constructor_layout.py`
- `experiments/vector-shape/probe-src/tools/verify_bee_newshape_task4_layout_undo_serializer.py`
- `datasets/ae-bee-newshape-task4-constructor-layout-2025-2026.json`
- `datasets/ae-bee-newshape-task4-undo-layout-verified-2025-2026.json`

No AE execution, private registrar calls or Adobe DLL edits occurred. Native CNL type registration, Comp ownership, Pen/Selection, BEE_VectorArt and foreign-object Undo remain **not implemented**. See F-VECTOR-058 for the built-in creation chain.
