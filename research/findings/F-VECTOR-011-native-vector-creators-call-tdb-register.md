---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L + E2-X contextual
versions: installed AE2025 and AE2026 BEE.dll/TDB.dll
---

# F-VECTOR-011 — Native vector Shape/Graphic/Filter stream factories are actually registered via TDB ScRegisterStreams

## Why this exceeds exported symbol discovery

Offline x64 executable-section scanning (AE2025: **4,488,162** instructions; AE2026: **4,626,191** instructions) found direct RIP-relative references to **31 of 33** target creator functions in each binary. Windows x64 `.pdata` unwind **function** boundaries grouped all 31 creator references into **exactly four** registration functions in **both** installed binaries, not an unreliable "nearest export" approximation.

| Group (meaning derived from creator families) | AE2025 native function | AE2026 native function | distinct typed creator references |
| --- | --- | --- | ---: |
| vector operators: Merge/Trim/Repeater/etc | `0x715E80–0x716882` | `0x738360–0x738D4A` | 13 |
| drawing properties: Fill/Stroke/Gradient/etc | `0x716890–0x717138` | `0x738D50–0x7395D7` | 8 |
| primitive/path group: Shape/Rectangle/Ellipse/Polystar | `0x717140–0x7174D0` | `0x7395E0–0x739958` | 5 |
| layer and vector group infrastructure: VectorLayer/Contents/Transform/Material | `0x77C630–0x77D338` | `0x79D040–0x79DD37` | 5 |

**Crucial confirmed static call edge:** disassembly of the four function bodies plus resolved PE Import Address Table showed repeated **direct imports to** `TDB.dll!TDB_ScRegisterStreams::Register`. There are 55 / 47 / 19 / 62 such static CALL sites respectively in AE2026. AE2025 exhibits 55 / 47 / 19 / 62 respectively. Each function does **many more registrations than only the exported 31 creator sites**; the registration counts are static instructions, not proof every code branch executes or every matched class is registered at runtime.

AE2026 operator example around `0x738395`:
- `lea rdx, [rip+...]` references a static `TDB_MatchName`-like registry key object.
- `lea r8, [rbp-0x48]` passes a stack-local C++ creator wrapper.
- `call [rip+...]` at `0x73839F` resolves to `TDB_ScRegisterStreams::Register`.
- Adjacent blocks load the addresses of built-in `BEE_VectorStream::*::Create` as callback pointers.

The `TDB_MatchName`-like references point into zero-initialized binary image data at rest; **the static file does not contain fully initialized runtime key objects**. Do not claim to recover actual C++ object layouts or runtime values from those zero-filled bytes. The decorated exports of the creator callbacks, not their adjacency alone, establish their factory signature.

The evidence establishes **Adobe's own built-in native vector stream kinds actually participate in the TDB registration mechanism**. This is no longer only type-generic TDB registry evidence. **Still not established:** third-party registration, arbitrary custom native VectorArt evaluation, or host tool edit binding.

## Reproducible raw data

- `datasets/ae-vector-stream-creators-static-xrefs-2025-2026.json` — precise creator instructions and code section scan.
- `datasets/ae-vector-creator-registration-bundles-2025-2026.json` — `.pdata`-bounded static CALLs to resolved TDB registration exports.
- `datasets/ae-native-vector-render-edit-boundary-2025-2026.json` — exported typed factory classes.
- Source-only analysis scripts: `experiments/vector-shape/probe-src/tools/trace_vector_creator_xrefs.py`, `group_creator_xrefs_by_unwind.py`, `trace_creator_registration_bundles.py`.
