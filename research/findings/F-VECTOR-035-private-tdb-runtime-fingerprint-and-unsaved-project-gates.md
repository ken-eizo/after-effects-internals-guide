---
status: compiled-offline-verified-NOT-host-tested-high-risk
last_verified: 2026-10-12
evidence: E2-B + E2-L + H
versions: exact installed AE2025/AE2026 TDB.dll, VS2022 SDK25.6
---

# F-VECTOR-035 — Unsaved-project isolation and live TDB code-entry attestation before private registration

## Question and result

Could the existing dangerous, **unexecuted** private TDB creator-registration AEX be made more resistant to accidental use in an important project, ABI drift in a patched runtime, and a second attempt after failed/unverifiable cleanup? Yes, to a limited extent. A new compiled/static-tested guard is available; **the private registrar has still NEVER been called in AE**.

The original standalone native geometry engine and read-only AEGP getter success remain the prior state (F-VECTOR-029/032 and EXP-SHAPE-028-LIVE-001). This finding DOES NOT establish an effect-owned native Contents root, native editable path, BEE evaluator, VectorArt output, or a reversible host mutation.

## New verified implementation (ShapeLayerAE)

The shared public-AEGP `NativeProjectSafety.h` predicate now calls `AEGP_GetProjectPath` and reads its UTF-16 result using `AEGP_MemorySuite1`, explicitly unlocks and frees the returned handle, rejects errors, and rejects ANY saved project path. This is in addition to one project, clean project, no non-root items, no active non-root item, zero Render Queue entries and read-only SDK success. Crucially, an empty but saved working .aep no longer qualifies.

`CNLPrivateTDBDisposable.cpp` now rejects a failed `AEGP_GetActiveLayer` query rather than treating it as no selected layer. It checks the project gate both before acknowledging and immediately after consuming the one-shot flag.

A second, independent in-memory fingerprint compares **16 mapped instruction bytes** at each of five exact private export addresses against 2025/2026 PE source fingerprints. The exported methods are: `Get_AE_StreamFactory`, `TDB_MatchName` string constructor, `TDB_ParamPathStream::Create`, `RegisterFactoryFunc`, and `UnregisterFactoryFunc`. The code checks committed, readable/executable pages; a mismatch fails closed. On-disk TDB SHA-256 verification and the corrected MSVC decorated `std::function<TDB_StreamBase*(TDB_MatchName const&, TDB_StreamFactory*, bool, unsigned, bool)>` contract remain mandatory.

The immutable PE evidence was extracted by `ShapeLayerAE/tools/audit_tdb_native_entry_fingerprints.py` and independently revalidated by the modified `verify_no_host_load.py` verifier against installed binary export RVAs. The cross-module Mock CTest and `verify_symbol_abi.py` again passed.

The mutating AEX now has a one-attempt per loaded plugin-module atomic gate. Subsequent menu commands cannot re-enter the private ABI after even a failed attempt in the same loaded module instance. Following unregister, it performs another read-only public project-state check and writes `private_registry_rollback_proven=0` regardless of the return code.

## Exact version provenance (E2-L, not live AE)

| Year | File SHA256 | Getter RVA | Register RVA | Unregister RVA |
| --- | --- | --- | --- | --- |
| AE2025 | `2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69` | `0x8100` | `0x27400` | `0x28bc0` |
| AE2026 | `82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b` | `0x81b0` | `0x285d0` | `0x29c10` |

Other entrypoint names, exact RVAs, and 16-byte fingerprints are captured in the experimental verifier and v3 build receipt.

## What remains UNSAFE / unknown

1. Correct exported function decoration and first 16 opcode bytes **cannot validate** hidden constructors, native class lifetime, exception behavior, private manager state, ABI of all call edges, or whether registration is permitted after BEE/TDB startup.
2. The shared SDK guard cannot prove no unsaved information outside the project or global cache. A separate disposable AE PROCESS is still required. The user alone may perform manual host tests and install AEX binaries.
3. `UnregisterFactoryFunc` returning `true` does not prove all canonical and creator objects, copies of erased `std::function`, backend maps, caches, undo entries and other host references are gone. No safe external private introspection contract for those maps has been demonstrated. Calling speculative `GetCanonicalInstance` itself is not accepted as a safe rollback proof.
4. Even a false return or crash before the logged unregister may leave mutated global state. The once-latch cannot survive a DLL reload/process restart, and **cannot guarantee rollback or unload safety**.
5. The updated safe read-only AEX was rebuilt, but its NEW unsaved-path project preflight has **not** been AE runtime tested. The previous v1 getter test remains verified.
6. Exact owner/Timeline/Pen selection/Undo and BEE VectorArt/AGM render subscriptions remain separate proof gates; these are not obtained by a TDB registry registration.

## Real new capability and falsification path

This improves the experimental basis for determining whether an external creator registration is **admissible** without depending on standard Masks or Shape Layers. If the registrar acceptance test eventually succeeds under separately authorized disposable host testing, the next falsifiable question is whether a new registered stream can acquire independent persistent owner identity rather than merely a canonical object.

Only after a real native owner exists could one probe Pen selection binding and the separate BEE MatchName/operator + VectorArt pipeline, toward a plugin-defined genuine vector object. Such a feature is a research possibility, not an accomplished product.

See EXP-SHAPE-033, F-VECTOR-025/026/028/031/034, EXP-SHAPE-031/032. Phase F (CompNodeAE integration) is deliberately deferred and no `D:/Developer/CompNodeAE` files were edited.

## Follow-up: AE2026 read-only host evidence and diagnostic refinement (2026-10-12)

The user ran the v3 `CNLNativeVectorHostProbe` in the real AE2026 process (EXP-SHAPE-034). The genuine TSV confirmed all prior read-only native CNL Bezier and factory-getter signals, while the disposable project gate returned `BLOCKED` specifically at `AEGP_ProjectIsDirty=1`. No TDB type mutation was invoked. `non_root_items=-1` and `render_queue_items=-1` reflect not-reached checks in that tested version, NOT verified empty content.

After this evidence, the shared public SDK gate was refined to continue reading path/root/items/Render Queue even when a project is dirty or has a saved path, then reject dirty or saved projects **at the end**. This preserves the hard blocking decision and improves diagnostics. The read-only AEX also reports saved-path/active-non-root flags, displays the exact rejection reason in its dialog, and fails SHA256 on Windows ReadFile errors. Both dependent AEX files were rebuilt and statically verified. These *newer* AEX versions have NOT been user-tested, and there is still no private registrar live result.

The precise 2025/2026 BEE_VectorLayer registration entrypoints and secondary evaluator initialization were also traced independently (F-VECTOR-036, EXP-SHAPE-035). That native owner/evaluator boundary has no verified foreign extension contract.
