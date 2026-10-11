---
status: confirmed-in-host
last_verified: 2026-10-11
evidence: E2-X + E2-L + E0-H
versions: AE2026/SDK25.6/ShapeLayerAE v3
---

# F-VECTOR-010 — An external AEGP obtained a non-null pointer from AE's private TDB factory getter

## Executed host experiment

At 2026-10-11 19:29:43 local, the user explicitly invoked **Animation > ShapeLayerAE: Probe Private TDB Getter (Read Only)**. The native After Effects dialog reported the receipt had been written. The observer archived the resulting **original byte-identical** `%TEMP%/ShapeLayerAE_private_factory_probe.tsv` at `experiments/vector-shape/runs/EXP-SHAPE-009-010/20261011-user-host-v3/`:

```text
module_found  export_found  code_fingerprint_ok  factory_pointer_nonnull
1             1             1                    1
```

Raw SHA-256: `390bb93c2de843cb55aa50983173e7af50348122a63d277bc81c1cefd8eba017`. The active AE host was `D:/Adobe/Adobe After Effects 2026/Support Files/AfterFX.exe`. Both installed AEX and locally built AEX had hash `6a20aaa59100a68aaa5e8aa4af126756a9dd8dd6cf50951dce8cf1bf6ec6dbf1` at observation, establishing the deployed v3 binary matches the source-built artifact.

The AEGP invoked `GetModuleHandleW(L"TDB.dll")`, `GetProcAddress` on `?Get_AE_StreamFactory@@YAPEAVTDB_StreamFactory@@XZ`, checked the five-byte instruction pattern plus relative displacement (`48 8B 05 [disp32] C3`), and called the **zero-argument getter only**. It recorded whether the pointer was nonnull; the pointer value was not recorded. No private object method was invoked, no factory memory dereferenced, no streams added/removed/registered.

## Evidential claim and limitations

**Now E2-X:** A standalone user-installed AEGP can resolve and call this version's undocumented native TDB global factory accessor and receive a non-null value. This is stronger than a symbol-export-only inference.

**Still H:** the pointer is a valid host-owned factory with a stable lifetime/usable C++ ABI at arbitrary plugin hooks; `RegisterFactoryFunc` may be called safely; a native custom stream persists; it is editable through AE's native Pen tool; or it feeds the AGM renderer. None follows merely from this getter result.

The accessor is private/unsupported, and no Adobe compatibility promise exists. The opcode check does not by itself validate the pointer's target object layout. Additional memory or method probes require a separate, isolated, opt-in experiment with explicit risk evaluation. The user did not run a private registration operation.

## Cross evidence

- `F-VECTOR-008-tdb-native-factory-registration.md` — internal registration chain.
- `datasets/ae-tdb-register-callsite-disasm-2025-2026.json` — exact private getter disassembly.
- `experiments/vector-shape/EXP-SHAPE-010-private-factory-getter-optin.md` — original design, updated to host-observed.
