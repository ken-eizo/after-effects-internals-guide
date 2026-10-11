---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: installed AE2025 and AE2026 BEE.dll / TDB.dll
---

# EXP-SHAPE-011 — Creator registration bundles by real x64 function boundaries

## Setup and objective

From each locally installed AE BEE.dll, resolve exported `BEE_VectorStream::*::Create(TDB_MatchName const&, TDB_StreamFactory*, ...)` functions, scan direct RIP-relative code references to their entry addresses, group matching instruction RVAs using the module's Windows x64 `.pdata` unwind function table, and resolve imported register calls using BEE's PE Import Address Table for **the corresponding AE version**. No native code executes.

## Reproducible evidence

- Whole-image static code scans: 4,488,162 instructions in AE2025 and 4,626,191 in AE2026.
- 33 selected export creators per version; 31 referenced by direct RIP-relative `lea` instructions.
- All 31 references fall into exactly **four x64 unwind-bounded functions**, in each build.
- Those four functions respectively contain **55, 47, 19, 62** direct `TDB.dll!TDB_ScRegisterStreams::Register` imported CALL sites in both builds.
- Example AE2026 site: the operator registration function from RVA `0x738360` prepares native typed creator wrapper & MatchName and calls `TDB_ScRegisterStreams::Register` at `0x73839F`.
- Therefore, built-in AE Shape/Graphic/Filter typed creators are **actually referenced as TDB registration callbacks in the native code**, not merely generic export signatures.

## Provenance

`datasets/ae-native-vector-render-edit-boundary-2025-2026.json` — hash `54E062D2117AEB8F4130A9F6A4308C33E05627A6F9A6738564503F50FC7F2474`

`datasets/ae-vector-stream-creators-static-xrefs-2025-2026.json` — hash `A678FE507CE6F29A2CAF420B1ADB7A114AE537D96F2341C181862D125863BDBB`

`datasets/ae-vector-creator-registration-bundles-2025-2026.json` — hash `B51DC197A4826AB399CC45A3FC294EF3F085730637BA39A1D3E7596940A92286`

Scripts: `experiments/vector-shape/probe-src/tools/audit_vector_render_editor_boundary.py`, `trace_vector_creator_xrefs.py`, `group_creator_xrefs_by_unwind.py`, and `trace_creator_registration_bundles.py`.

## Falsification and next step

The strongest justified E2-L conclusion is internal Adobe-native creator registration. External AEGP getting a pointer from `Get_AE_StreamFactory` does **not** establish a stable creation callback ABI. Next evaluate separately: MatchName construction, registry ownership, canonical prototype creation, subtype vtables/destructors, serialization and native render dispatch before attempting any mutation in a disposable host.
