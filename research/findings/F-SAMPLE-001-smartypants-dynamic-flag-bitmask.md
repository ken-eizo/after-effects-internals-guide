---
status: source-repair-verified
last_verified: 2026-09-22
evidence: AE-25.6-distributed-sample + sibling-sample comparison
---
# F-SAMPLE-001 — SmartyPants likely contains a Dynamic Flags bitmask defect

`SmartyPants::QueryDynamicFlags()` executes `out_data->out_flags2 &= PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS` when its channel parameter selects alpha.

That expression retains only the target bit; it does not clear the target bit. In the same AE 25.6 SDK, `Resizer::QueryDynamicFlags()` uses the conventional and semantically expected clear form `out_flags2 &= ~FLAG` for dynamic 3D flags.

SmartyPants' Global Setup and PiPL do not advertise `PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS`, making the line especially suspicious: absent host-provided state, the expression can collapse unrelated dynamic bits while still failing to set the intended bit.

## Confidence
High confidence as a source-level logic defect candidate. Runtime impact remains host-contract dependent and should be measured before labeling it an observable AE bug.

## Test
Instrument Query Dynamic Flags, record incoming/outgoing `out_flags2`, toggle the Alpha channel, and compare cache/bounds behavior against a corrected local build using `|=` or `&= ~` according to intended semantics.
## Source-level verification, 2026-09-22

experiments/sdk-contract-fixes pins the source and checks the exact QueryDynamicFlags body over 1048576 input-mask/channel/error cases. Clearing with the complemented target mask preserves unrelated bits; the original fails 262143 cases and the corrected source fails none. The repair chooses clear semantics because Alpha may produce nonempty output from zero-alpha input.

This supersedes the candidate-only algebra assessment above. The current SmartFX Guide treats DOESNT_NEED_EMPTY_PIXELS as obsolete; no current-host bounds/cache effect is inferred. The proposed host test remains a separate gate. See [scoped sample repairs](../../docs/host-integration/cpp-sdk/verified-sample-repairs.md).
