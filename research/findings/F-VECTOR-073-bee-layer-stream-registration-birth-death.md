---
date: 2026-10-14
status: PASS pinned native AE2025/2026 built-in BEE stream registration birth/death direct-call chain
evidence: E2-L full dumpbin export tables, x64 PE .pdata + Capstone instruction-boundary-validated E8 calls, SHA-256
---
# F-VECTOR-073 — Built-in BEE Layer/AV/Text/Vector stream types register during BEE_Birth and tear down during BEE_Death

## Key result

The first native BEE Layer owner lifecycle is now independently traced through both real installed Adobe binaries, not inferred only from export names or hypothetical plugin callbacks.

In both AE2025 and AE2026, one **unexported common startup helper** is called directly from the exported `BEE_Birth`. That helper calls the registered native `BEE_Layer::RegisterStreams`, `BEE_AVLayer::RegisterStreams`, `BEE_TextLayer::RegisterStreams` and `BEE_VectorLayer::RegisterStreams` routines.

A separate **unexported common teardown helper** is called directly from exported `BEE_Death`; it calls `BEE_Layer::RegisterStreams(bool)` again and the explicit `BEE_AVLayer::UnregisterStreams`, `BEE_TextLayer::UnregisterStreams` and `BEE_VectorLayer::UnregisterStreams` routines.

### Exact native startup and teardown RVAs

| Native stage | AE 2025 | AE 2026 |
| --- | --- | --- |
| `BEE_Birth` enclosing function | `0x64A530` | `0x664F70` |
| Direct call into common startup helper | `0x64AAE0` | `0x66551B` |
| Common stream startup helper | `0x36DD90` | `0x3787B0` |
| `BEE_Layer::RegisterStreams` call | `0x36DE21` | `0x378841` |
| `BEE_AVLayer::RegisterStreams` call | `0x36DE29` | `0x378849` |
| `BEE_TextLayer::RegisterStreams` call | `0x36DE33` | `0x378853` |
| `BEE_VectorLayer::RegisterStreams` call | `0x36DE38` | `0x378858` |
| `BEE_Death` enclosing function | `0x64B090` | `0x6659A0` |
| Direct call into common teardown helper | `0x64B1AD` | `0x665ABD` |
| Common stream teardown helper | `0x36DEF0` | `0x378910` |
| Teardown call to `BEE_Layer::RegisterStreams(bool)` | `0x36DEFC` | `0x37891C` |
| `BEE_VectorLayer::UnregisterStreams` call | `0x36DF10` | `0x378930` |
| `BEE_TextLayer::UnregisterStreams` call | `0x36DF15` | `0x378935` |
| `BEE_AVLayer::UnregisterStreams` call | `0x36DF1F` | `0x37893F` |

BEE native DLL hashes are stored in the JSON dataset. These are **direct compiled CALL instructions** with decoded instruction boundaries, not only byte-pattern matches and not dynamically observed call counts.

## Important interpretation

Adobe's built-in native Layer-family TDB registration is coupled to BEE module **birth/death** lifecycle. This adds a new native-code explanation for why publicly adding `AEGP_Menu_NEW` or providing a separate CNL native C++ type is NOT enough to join the Adobe Layer family.

This does **not** mean TDB has no other registration API (F-VECTOR-008 confirms a private generic factory registry). Nor does it prove no alternative indirect, cross-module or unexported plugin registration path exists. It establishes exactly where these **four built-in owner families** register and unregister. Registration during BEE startup should not be confused with a supported, late third-party AEGP plugin registration contract.

F-VECTOR-037 and F-VECTOR-071 still independently block a simplistic ninth-layer-kind or arbitrary cloned foreign pointer approach; the public SDK audit F-VECTOR-072 found no native owner class registration suite in the installed SDK.

## Methodology correction with future research implications

The BEE DLLs expose **13,647** (AE2025) and **14,182** (AE2026) decorated exports through the full `dumpbin /exports` view. The installed `pefile` Python library had `MAX_SYMBOL_EXPORT_COUNT = 8192` and enumerated only that many via the default `DIRECTORY_ENTRY_EXPORT` traversal. This initially incorrectly made all later alphabetical `RegisterStreams` symbols invisible. The audit was corrected to obtain ALL export names with `dumpbin` before target discovery.

Any negative assertion about the existence of exported BEE registration functions based solely on default pefile symbol enumeration is unsound. The new checker fails if the full export census or expected native registrars are missing, and validates each candidate relative CALL against disassembly of the actual containing PE unwind function.

## Reproduction

- `experiments/vector-shape/probe-src/tools/audit_native_layer_birth_death_registration.py`
- `experiments/vector-shape/probe-src/tools/verify_native_layer_birth_death_registration.py`
- `datasets/ae-bee-native-layer-stream-birth-death-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-073-bee-stream-registration-birth-death.md`
- `experiments/observatory/manifests/EXP-SHAPE-073.json`

All analysis is read-only from the pinned installed DLL files; no private C++ host functions are invoked, Adobe modules modified, or unsafe AEX installed. External BEE_Layer subclass admission, native editor and renderer integration remain UNPROVEN.

## Next falsification targets

Trace incoming edges/arguments to `BEE_Birth` (including other modules and potential plugin bootstrap contracts), and independently distinguish static built-in registration from any allowed runtime third-party registrar. Recover exact foreign-type ownership and guaranteed unregister lifecycle before considering an in-host prototype. No user After Effects GUI operation is authorized by this evidence.
