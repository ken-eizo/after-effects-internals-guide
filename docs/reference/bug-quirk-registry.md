---
status: generated
last_verified: 2026-09-17
---
# AEIG Bug / Quirk / Regression Registry

Curated entries: **32**. Fixed: **15**. Non-fixed / contract / historical entries: **17**.

This registry is an evidence index, not a claim that AEIG knows every After Effects bug. A symptom identifies a boundary to investigate; it does not by itself prove a private root cause.

## Source classes

| Source type | Entries |
|---|---:|
| `adobe-fixed-issue` | 14 |
| `sdk-contract-warning` | 7 |
| `adobe-known-issue` | 2 |
| `sdk-sample-pitfall` | 2 |
| `adobe-sdk-known-issue` | 1 |
| `sdk-contract-quirk` | 1 |
| `aeig-finding` | 1 |
| `sdk-contract-lifecycle` | 1 |
| `sdk-contract-pitfall` | 1 |
| `historical-abi-bug` | 1 |
| `historical-compat-quirk` | 1 |

## Subsystem coverage

| Subsystem family | Entries |
|---|---:|
| `3d` | 4 |
| `image` | 4 |
| `cache` | 3 |
| `ai-analysis` | 2 |
| `text` | 2 |
| `media` | 2 |
| `smartfx` | 2 |
| `state` | 2 |
| `cache-system` | 1 |
| `tracking-analysis` | 1 |
| `observability` | 1 |
| `pica` | 1 |
| `gpu` | 1 |
| `headless` | 1 |
| `mfr` | 1 |
| `streams` | 1 |
| `effect` | 1 |
| `ui` | 1 |
| `tracking` | 1 |

## Registry

| ID | Status | Subsystem | Symptom | Boundary / rule | Evidence |
|---|---|---|---|---|---|
| `BQ-0001` | `fixed` | `ai-analysis/headless` | aerender failed to render compositions containing Object Matte | analysis persistence/headless render integration; Use a fixed host version; treat headless support as an independent capability boundary | F-AI-001 |
| `BQ-0002` | `fixed` | `ai-analysis/state` | Object Matte added spurious Set Stream Flags undo steps | analysis UI/project-stream mutation boundary; Do not infer internal stream mutations are user-visible semantic edits | F-AI-002 |
| `BQ-0003` | `fixed` | `text/cache` | expression-driven text style edits could leave existing cache frames stale | expression dependency/text render identity/cache invalidation; Version-scope cache/invalidation tests for expression-driven text style | F-TEXT-002 |
| `BQ-0004` | `known/mitigated` | `cache-system` | some configurations crashed with Lossless Compressed Disk Caching enabled | disk-cache codec/backend compatibility; Use hardware fallback/fixed versions; keep compressed/uncompressed paths separate in evidence | F-CACHE-002 |
| `BQ-0005` | `fixed` | `cache/memory` | Empty Disk/3D/All Caches could freeze while scanning large slow or network cache | purge control loop/filesystem latency/UI progress; Treat purge as asynchronous/resource-control work rather than one blocking free | F-CACHE-014 |
| `BQ-0006` | `fixed` | `media/cache` | cleaning media cache could hang when entries referenced unsynced OneDrive files | cache cleanup/external filesystem availability; Model cache cleanup as external-I/O tolerant; do not assume local synchronous files | Adobe fixed issues 26.5 |
| `BQ-0007` | `fixed` | `tracking-analysis` | mask tracking could fail when composition Resolution was below Full | analysis sampling/downsample/coordinate mapping; Record preview/downsample state independently from source-analysis state | F-TRACK-001 |
| `BQ-0008` | `fixed` | `3d/state` | Essential Property values were shared across precomps in the same 3D bin with Collapse Transformations | instance/context identity under collapsed 3D rendering; Test per-instance render identity under collapsed/shared-bin contexts | F-3D-002 |
| `BQ-0009` | `fixed` | `3d/render` | scenes too complex for the render engine could crash AE | renderer resource/admission/error boundary; Treat renderer feasibility/resource limits as explicit failure states | Adobe fixed issues 26.5 |
| `BQ-0010` | `fixed` | `3d/render` | enabling Draft 3D with collapsed nested comps could crash | collapsed-context/render-bin/renderer interaction; Use topology-specific regression fixtures for collapsed 3D paths | F-RENDER-004 |
| `BQ-0011` | `fixed` | `3d/render-order` | coplanar 3D layer render order differed between Advanced and Classic 3D | renderer-specific ordering policy; Do not infer one universal 3D ordering policy from timeline order | Adobe fixed issues 26.5 |
| `BQ-0012` | `fixed` | `text/font` | variable-font expression animation slowed performance and created extra font-style menu entries | font-axis/style materialization and identity; Record font resource/axis state in expression/text performance tests | F-TEXT-002 |
| `BQ-0013` | `fixed` | `media/image` | tiled EXR footage could produce incomplete frames | decode/tile assembly/frame completeness; Use tiled-media fixtures when validating importer/frame completeness | Adobe fixed issues 25.5 |
| `BQ-0014` | `fixed` | `observability` | Help > Reveal Logging Files could crash more than 24 hours after logging was enabled | logging lifecycle/path/session rollover; Treat observability tooling as mutable runtime state with its own failure modes | Adobe fixed issues 25.3 |
| `BQ-0015` | `fixed` | `smartfx/bounds` | checkout_layer during SMART_PRE_RENDER could return empty rects | pre-render checkout/bounds contract; Historical workaround was retry; no longer needed from 11.0.1 | SmartFX Guide historical note |
| `BQ-0016` | `active-risk` | `cache/threading` | render can consume state different from the last QUERY_DYNAMIC_FLAGS response | dynamic capability generation/render identity; Snapshot dynamic state; return flags and render from the same generation | F-CACHE-010 |
| `BQ-0017` | `active-contract` | `state/threading` | state query returns randomized/unreliable state in unsafe UI context | UI/render synchronization/deadlock boundary; Do not derive render cache identity synchronously from UPDATE_PARAMS_UI | F-THREAD-002 |
| `BQ-0018` | `active-contract` | `image/convolution` | REPLICATE_BORDERS and ALPHA_WEIGHT_CONVOLVE are defined but ignored; only USE_LONG coefficient mode implemented | declared API surface versus implemented host semantics; Implement required border/alpha semantics yourself; test behavior rather than enum presence | F-KERNEL-001 |
| `BQ-0019` | `historical-pitfall` | `pica/suites` | deprecated suite handler acquisition/release behavior can leak suite references | PICA suite ownership/lifetime; Prefer AEFX_SuiteScoper or exact balanced acquisition/release | F-DESIGN-002 |
| `BQ-0020` | `sample-pitfall` | `cache/hash` | sample passes sizeof(const char*) where textual tag length may have been intended | cache-key construction/sample correctness; Hash explicit byte count/string contents; never copy sample code without C/C++ semantic review | Compute Cache sample |
| `BQ-0021` | `active-contract` | `smartfx` | resources allocated as if Render must follow PreRender can leak or corrupt state | planning/execution lifetime boundary; Transfer pre_render_data ownership to AE and support PreRender-only paths | F-RG-003 |
| `BQ-0022` | `active-contract` | `gpu/image` | dereferencing PF_LayerDef.data during GPU Smart Render is invalid | CPU pointer versus GPU residency; Use GPU device/world access; data is null by contract | F-GPU-005 |
| `BQ-0023` | `active-contract` | `state/handles` | long-lived Layer/Stream/queue refs can become invalid after structural changes; even keyframe edits can invalidate stream refs | opaque handle lifetime versus semantic identity; Store durable IDs/paths where documented and reacquire handles | F-STATE-002 |
| `BQ-0024` | `active-contract` | `headless/aegp` | saved opaque handles can collide/lose process-instance meaning when command-line AE instance duplicates handles | process identity versus handle identity; Associate retained host state with plug-in/AE instantiation; avoid serialized handles | F-HEADLESS-001 |
| `BQ-0025` | `active-contract` | `mfr/state` | mutations made to compatibility render sequence copies are not shared/durable across render threads | MFR sequence ownership; Use const render state plus Compute Cache/shared explicit synchronization for derived data | F-THREAD-003 |
| `BQ-0026` | `active-contract` | `image/convolution` | in-place use of WorldTransform convolve violates host contract | image buffer ownership/aliasing; Use separate output/intermediate world | F-KERNEL-001 |
| `BQ-0027` | `active-contract` | `image/memory` | assuming tight rows or writing beyond indicated region can modify unrelated cached image data | image-world allocation/cache alias boundary; Always use rowbytes and declared region; test with Grow Bounds | PF_EffectWorld Guide |
| `BQ-0028` | `historical` | `streams/abi` | compiler inserted extra padding in AEGP_StreamValue requiring forced packing workaround | binary ABI/compiler layout; Never serialize native structs or assume compiler packing across SDK generations | F-STREAM-002 |
| `BQ-0029` | `sample-pitfall` | `effect/dynamic-flags` | Adobe sample likely mutates dynamic flag mask incorrectly in one path | sample code versus contract; Treat sample as expected-use evidence not infallible reference implementation | F-SAMPLE-001 |
| `BQ-0030` | `historical-compat` | `image/transfer` | distributed SDK retains intentionally wrong transfer-mode macro for compatibility | ABI/behavior compatibility debt; Use corrected modern path unless reproducing legacy behavior intentionally | F-DESIGN-003 |
| `BQ-0031` | `known` | `ui/persistence` | Shape or Camera layer twirl state may reopen collapsed | project migration versus per-view/editor persistence; Restore twirl state manually and re-save project in current version | Adobe known issues 26.5 |
| `BQ-0032` | `fixed` | `tracking/mask` | new Mask Tracker failed when composition Resolution was less than Full | analysis sampling resolution versus semantic mask coordinates; Use 26.5+; test tracker semantics independently of preview resolution | F-TRACK-001 |

## Editorial rules

1. Fixed/known issue wording is behavioral evidence, not automatic proof of root cause.
2. Unsupported SDK/sample behavior is labeled as a contract warning or pitfall rather than public functionality.
3. Version scope is mandatory. Historical quirks are not silently described as current behavior.
4. Add a Finding when a bug materially supports an architectural conclusion; keep the registry row as the symptom/version index.
5. Preserve unknowns. If no workaround or cause is established, say so rather than inventing one.

Machine-readable registry: `datasets/aeig-bug-quirk-registry.csv`. Curated source: `research/bug-quirks.csv`.
