---
date: 2026-10-14
status: PASS pinned AE2025 and AE2026 native BEE_Birth argument consumer separation
evidence: E2-L BEE.dll x64 .pdata and Capstone direct-call contract, module SHA-256, cross-version verifier
---
# F-VECTOR-076 — BEE_Birth's byte-map initialization is separate from native Layer stream registration

## Product-level question

Does `BEE_Birth(const unsigned char*, const map<string,bytes>&, unsigned, int, bool)` receive a map of foreign native Layer constructors / TDB types, so that an independent ChapeLayer could be admitted by adding its own entry?

The full exported MSVC signature proves the second argument really is a `std::map<std::string, std::basic_string<unsigned char,...>> const&`. **A byte map is not automatically a registry of executable C++ creators.** We therefore followed its exact native consumption rather than inferring an API from the parameter type.

## Exact cross-version evidence

| Native observation | AE2025 | AE2026 |
| --- | --- | --- |
| Exported `BEE_Birth` entry RVA | `0x64A530` | `0x664F70` |
| Input byte-map pointer preserved | `[rsp+0x38]` | `[rsp+0x88]` |
| `mov rcx, saved map` then call helper | `0x64AAC9` | `0x665507` |
| Separate map helper RVA | `0x11BEE0` | `0x122910` |
| Original first pointer argument preserved | `[rsp+0x158]` | `[rsp+0x40]` |
| `mov rcx, saved first pointer` then call built-in family registration helper | `0x64AAE0` | `0x66551B` |
| Built-in family registration helper RVA | `0x36DD90` | `0x3787B0` |

The map helper executes **before** the built-in family registration call in both versions. The map helper's decoded native body invokes imported `sccore.dll` `Localizer` methods and `extendscript.dll` / ScScript init facilities. It also manipulates a host-side associative container and initializes other infrastructure. A direct call to `TDB_ScRegisterStreams` or `TDB_StreamFactory::RegisterFactoryFunc` was not found in the inspected helper import calls.

In contrast, the **different** common native Layer bootstrap called later contains the direct calls to `BEE_Layer::RegisterStreams`, `BEE_AVLayer::RegisterStreams`, `BEE_TextLayer::RegisterStreams`, `BEE_VectorLayer::RegisterStreams` previously validated in F-VECTOR-073.

## Interpretation

This is direct evidence **against the earlier shortcut hypothesis** that supplying an extra key in the byte-map argument is itself a supported way to register a new `BEE_Layer` subclass. The inspected call graph uses the byte map for a separate initialization path with localizer/script initialization, while type-family stream registration follows a different hard-coded native call chain.

The **complete contents and meaning** of the byte map have NOT been reconstructed. The analysis does not rule out indirect factory calls or any entirely separate private registration route. It does not prove that the byte map cannot contain other configuration data. It proves that the observed native direct-call paths are distinct and that no external Layer creator registration contract has been demonstrated through the map.

This is consistent with:
- F-VECTOR-037: fixed eight-way native `BEE_Layer::CreateLayerFromType`;
- F-VECTOR-071: version-varying CompItem attachment ABI;
- F-VECTOR-072: no foreign native Layer class registrar in inspected public AEGP SDK;
- F-VECTOR-073/074/075: native Layer-family registration is reached through aelib -> BEE birth lifecycle.

## Verification and safety

Verifier: `experiments/vector-shape/probe-src/tools/verify_bee_birth_map_vs_layer_register.py`

Dataset: `datasets/ae-bee-birth-map-versus-layer-bootstrap-2025-2026.json`

Experiment: `experiments/vector-shape/EXP-SHAPE-076-bee-birth-map-and-stream-paths.md`

The verifier requires the **exact SHA-256 of both installed BEE DLLs**, checks actual machine instructions and relative CALL targets, verifies preserved argument provenance and searches the separate helper's PE-imported localizer/script functions. It passed for both host versions. No private Adobe calls, module injection, host registration experiments, or user document edits occurred.

## Next decisive investigation

The still-missing capability is a safe **foreign Layer class provider** accepted by an unmodified host, including an exact creation ABI, RTTI, ownership, per-version virtual method implementation, TDB serialization, VectorArt evaluation, Undo and deterministic unload. Additional observations of built-in registration must not be mislabeled as an implemented independent ChapeLayer.

If no supported external provider API is available, the honest product conclusion must be that full independent native Layer family support **cannot be delivered via the documented extension SDK**, and the only correct resolution is an Adobe-supported extension contract, a licensed/internal API arrangement, or a clearly separate non-native architecture explicitly accepted by the project owner.
