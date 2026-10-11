---
status: source-index
last_verified: 2026-10-11
---
# Shape native extension / forgotten API historical evidence, 2026-10-11

| ID | Class | Source | Supports | Excludes |
| --- | --- | --- | --- | --- |
| SH-HIST-01 | E0-G | AdobeDocs AE feature history: https://github.com/AdobeDocs/after-effects-feature-history | 1995 Bezier masking and 2007 CS3 native Shape Layer feature chronology | Exact 2007 internal code and third-party extensibility |
| SH-HIST-02 | E1-A | Chris & Trish Meyer, 2007 Shape Layers: https://www.provideocoalition.com/shape_layers/ | Contemporaneous CS3 feature/Vector Contents behavior | Specific host class factory internals |
| SH-HIST-03 | E0-G | Adobe current Working With Paths: https://ae-plugins.docsforadobe.dev/effect-details/working-with-paths/ | Public mask path query/checkouts | Direct vector renderer output and new Contents type |
| SH-HIST-04 | E0-H | `research/external-sources/ae-sdk-cs6/Headers/AE_EffectSuites.h`, PF Path suites version 1 frozen in AE 5.0 | Ancient path suite API lineage | Shape Layer model existing before 2007 |
| SH-HIST-05 | E0-H | CS6, CC2014 local archive and SDK 25.6 `AE_GeneralPlug.h` | Public grouping enum incl NONE=-1, leaf precondition, existing indexed-group mutation | External arbitrary factory registration |
| SH-HIST-06 | E0-S | Adobe Streamie SDK sample under `E:\ae25.6_61.64bit.AfterEffectsSDK\Examples\AEGP\Streamie` | Intended public stream traversal/reorder | Custom native type plugin registration |
| SH-HIST-07 | E2-L | Two installed BEE.dll binaries and `datasets/ae-shape-native-extension-lineage-2026.json` | Layer-type `RegisterStreams` exports and version-shifted RVAs | Callable private ABI, extension support |
| SH-HIST-08 | E2-L | `datasets/ae-vector-registerstreams-static-2025-2026.json` | Bounded disassembly suggests command-registration workload | Definitive call/dataflow or semantic identity |
| SH-HIST-09 | E3 | User-supplied 2026-10-11 AE dialog: `{GetNumStreamsInGroup only works on groups}` | Incident to compare against exact SDK precondition | Independently captured post-fix host behavior |
| SH-HIST-10 | E2-T | https://github.com/pushREC/after-effects-sdk-kb/blob/main/wave-3/07-text-shape-layers.md | Community exploration of shape stream hierarchy | ABI fact: its `NONE=0` enum conflicts with SDK 25.6's `NONE=-1` |

Key investigation rule: provenance is **claim-scoped**. A C++ export is an implementation artifact, not a supported SDK. A third-party snippet cannot override a distributed Adobe header. No forbidden Adobe proprietary sources are redistributed here.
