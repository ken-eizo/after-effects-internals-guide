---
status: confirmed-in-host
last_verified: 2026-10-11
evidence: E2-L + E2-X
versions: SDK25.6, optional AE2025/AE2026 exact private getter
---
# EXP-SHAPE-010 — Optional in-host read-only private TDB factory getter

`ShapeLayerAE` includes a separate, deliberately explicit Animation menu command `ShapeLayerAE: Probe Private TDB Getter (Read Only)`. It is **never invoked during plugin startup or ordinary tree traversal**.

On Windows x64, if `TDB.dll` is already loaded in the process, it calls `GetProcAddress` for `?Get_AE_StreamFactory@@YAPEAVTDB_StreamFactory@@XZ`. Before any call it checks the exact instruction shape observed for the **two pinned installed runtimes**: `48 8B 05 [disp32] C3`, corresponding to `mov rax,[rip+disp32]; ret`. If the fingerprint differs, **no private call occurs**. If it matches, it calls this *zero-argument getter only* and records whether the returned pointer is non-null.

The code never dereferences, saves, publishes, invokes methods on, creates or mutates the private factory pointer. There is no `TDB_ScRegisterStreams::Register` or `TDB_StreamFactory::RegisterFactoryFunc` invocation in this project.

Output: `%TEMP%\ShapeLayerAE_private_factory_probe.tsv`, four Booleans: module loaded, export present, fingerprint match and non-null factory pointer.

**Risks/limits:** this is still **private unsupported ABI**, even though the callsite is simple and guarded. It is not an Adobe-endorsed operation, may be unavailable/change in other builds, and would not prove external registration or editor/render integration. Do not execute on a production AE session/project; user must explicitly choose the command in a disposable project with no unsaved work. The host currently running has NOT been injected or restarted by this research session.

**Observed outcome:** on 2026-10-11 the user's AE2026 host reported `1/1/1/1`: TDB module found, private exported getter found, fingerprint matched and getter returned non-null. This establishes a third-party AEGP can call the private no-argument getter, **not** that a custom stream is registered. Raw TSV and hashes: `experiments/vector-shape/EXP-SHAPE-009-010-v3-host-confirmation.md`.
