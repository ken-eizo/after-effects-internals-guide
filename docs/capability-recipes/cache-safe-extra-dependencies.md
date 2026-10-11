---
status: active
last_verified: 2026-09-23
---
# Recipe: Make Non-Parameter State Cache-Safe

## Goal
Render depends on state AE cannot infer from ordinary parameter/stream checkouts: external configuration, host state, custom data or another semantic context.

## Supported SmartFX route
Set `PF_OutFlag2_I_MIX_GUID_DEPENDENCIES` and, during SmartFX PreRender, mix only render-relevant bytes through `GuidMixInPtr`.

The public contract explicitly says these bytes contribute to AE's internal cached-frame GUID. This is preferable to disabling caching whenever the extra dependency can be represented deterministically.

## Rules
- Mix stable semantic data, not pointer addresses.
- Use the **effective render context**, not merely project parentage.
- Include every external value that can change pixels; omit values that only affect UI/logging.
- Keep encoding/versioning deterministic so A→B→A can recover the same identity when appropriate.

## Temporal state
For time-dependent upstream inputs, use checkout/state APIs so AE can register the actual temporal footprint. `GuidMixInPtr` is not a substitute for declaring source-time dependencies.

A different case is an effect whose own semantic program reads **the current render time itself** as non-parameter state. The public `PF_OutFlag_NON_PARAM_VARY` contract explicitly names current frame time as a reason to set the bit. If only some effect instances use that dependency, advertise `PF_OutFlag2_SUPPORTS_QUERY_DYNAMIC_FLAGS` and answer `PF_Cmd_QUERY_DYNAMIC_FLAGS` from the same persisted/versioned configuration that render will consume instead of setting `NON_PARAM_VARY` globally for every instance.

For a host-independent language/runtime, prefer binding AE time into an ordinary typed scalar formal at the host boundary rather than adding a host-specific `time()` intrinsic to the language. Resolve the actual from `in_data->current_time / time_scale` for the render request, and include that concrete actual in any extra SmartFX GUID contribution used by the effect. This preserves static-frame cache reuse for instances that do not bind time while making time-bound instances vary correctly.

## Historical warning
Adobe's SmartyPants sample mixes parent-comp background color but warns that its example does not handle collapsed-comp context. Collapse Transformations can make project topology differ from render topology.

## Internal correlation
TDB/BEE expose stream/time GUID mixing and Render GUID formation, strongly supporting a compositional render-identity model. Their internal functions are not required to implement this recipe.

## Failure symptom
Under-mixing gives stale cache hits; over-mixing gives unnecessary misses. Unconditional cache invalidation hides both errors but loses reuse.

Related: `F-CACHE-015`, `F-GUID-003`, `docs/evaluation/dirty-invalidation.md`.

## Version and lifecycle discipline
`GuidMixInPtr` participates in SmartFX render identity during PreRender, so the bytes mixed must describe the same semantic generation that Render will consume. Mixing mutable external state and then rereading it later creates the same class of generation race as dynamic output flags.

Version your mixed payload explicitly when its encoding or algorithm changes. Otherwise two plug-in builds can interpret identical bytes differently while producing the same host-visible dependency hash.

Do not include process addresses, allocator layout, timestamps or randomized IDs unless they are genuinely part of pixel semantics; those values destroy A→B→A cache convergence.

## Choosing the right host mechanism
Use ordinary parameter/checkouts for host-visible dependencies, automatic wide-time checkout for temporal inputs, `PF_GetCurrentState` for selected host state and GUID mixing only for extra semantic dependencies AE cannot infer otherwise.

A useful rule is: **register dependency through the most semantic host surface available, and hash only what remains invisible to that surface**.

## Failure matrix
- omitted external value -> stale cached frame;
- pointer/random value mixed -> permanent cache fragmentation;
- render-context value taken from project parent instead of effective context -> wrong reuse under Collapse Transformations/precomp contexts;
- temporal source hashed as one current value -> misses dependency interval changes;
- payload encoding changed without version tag -> cross-build identity collision.

## Experiment
Create an external deterministic scalar that affects pixels but is absent from PF parameters. Exercise A→B→A with and without `GuidMixInPtr`, then repeat through Undo, project reopen and collapsed/nested contexts. Compare render callback count, output hash and receipt/Render-GUID evidence.

The expected behavior for a correct semantic key is stale-reuse prevention on A→B while allowing A to converge back to the earlier identity when all render-relevant state truly matches.

## Unknown frontier
The public contract does not expose how mixed bytes are combined with the rest of AE's frame identity, whether the exact same GUID feeds BEE/RG caches, or how implementation/build identity is partitioned internally. Treat the API as a semantic dependency contribution, not a public serialization of the complete key.
