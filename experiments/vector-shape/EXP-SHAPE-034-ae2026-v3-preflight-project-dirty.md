---
status: AE2026-host-verified-public-gate-blocked
last_verified: 2026-10-12
evidence: E2-X
versions: installed AE2026; host preflight AEX v3
---

# EXP-SHAPE-034 — AE2026 read-only vector preflight succeeds but dirty-project isolation blocks

## Host execution

User manually installed and launched `CNLNativeVectorHostProbe.aex` in After Effects 2026. The reported dialog read: `Bezier=YES, pinned TDB=2026, factory getter=1, empty-project gate=BLOCKED. Adobe native type NOT registered.` The full host-produced `%TEMP%/CNL_NativeVector_HostPreflight.tsv` was independently read from the authorized Windows PC and archived without edits at `experiments/observatory/runs/EXP-SHAPE-034/host-preflight-live-20261012-051447.tsv`.

Actual file modification time: 2026-10-12 05:14:47 local. No private registry mutation occurred.

## Confirmed values

| Observed TSV field | Observed value |
| --- | --- |
| tdb_module_loaded | 1 |
| tdb_sha256 | 82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b |
| pinned_AE_TDB_year | 2026 |
| private_factory_getter_export | 1 |
| getter_exact_opcode_pattern | 1 |
| getter_factory_pointer_nonnull | 1 |
| disposable_project_gate_pass | 0 |
| disposable_project_gate_reason | project_dirty |
| disposable_project_count | 1 |
| disposable_project_is_dirty | 1 |
| disposable_non_root_items | -1 (not reached) |
| disposable_render_queue_items | -1 (not reached) |
| CNL_document_created | 1 |
| CNL_double_bezier_cubic_status | 0 |
| CNL_native_cubic_segment_count | 4 |
| CNL_procedural_document_archive_bytes | 373 |
| private_registry_registration_invoked | 0 |
| new_native_host_stream_created | 0 |

A blocked project check does **not** mean the independent geometry or read-only factory getter failed. `CNL_CheckDisposableProject` returns early on `AEGP_ProjectIsDirty==TRUE`, so the TSV's `-1` item/queue counts mean **not inspected**; neither zero items nor zero Render Queue can be inferred from this run.

## Engineering response

Keep the high-risk registrar blocked for dirty projects. No registry experiment was attempted. Update the safe read-only preflight's dialog to include `projectGate.reason` and correct `exeModuleSHA256` so an interrupted Windows ReadFile produces a failed hash rather than an accidentally accepted partial digest. Compile/verify the new safe AEX offline; this newly rebuilt dialog is NOT yet AE host tested. No request to re-run the dangerous experiment is appropriate.

The host observation establishes F-VECTOR-035's conservative SDK project gate actually rejects a dirty project in AE2026, not that an unsaved completely empty project can pass the entire gate.

## Broader goal still pending

Neither real host Contents registration, third-party editable path, BEE evaluator installation nor native VectorArt output was exercised. Independent plugin-owned BEE vector objects remain the target, but Phase F code is intentionally out of scope until a genuine owner-editor-renderer bridge is proven.
