---
date: 2026-10-14
status: PASS pinned AE2025/2026 aelib native BEE_Birth call argument setup; semantic ownership not yet recovered
evidence: E2-L real installed aelib.dll Capstone disassembly, .pdata bounds, local SHA-256, four callsites
---
# F-VECTOR-075 — aelib BEE_Birth supplies version-gated initialization arguments at two native callsites per AE version

## Discovery

F-VECTOR-074 established that two callsites in each version's `aelib.dll` invoke the imported `BEE_Birth`. For both callsites in AE2025 and AE2026, the machine instructions immediately before the native CALL show a **consistent four-register argument arrangement**, a build-specific immediate in `r8d`, one more value from native global state in `r9d`, and a conditionally materialized boolean stack argument. A subsequent `test eax,eax` checks the return status.

The two tested callsites in each version have the **same immediate**:

| Version | First/second BEE_Birth callsite | r8d constant | Outcome |
| --- | --- | --- | --- |
| AE2025 | `0x6E272` / `0x6F6CF` | `0x0F0B2603` | Both pass verifier |
| AE2026 | `0x70647` / `0x71BC8` | `0x0F118657` | Both pass verifier |

Each inspected setup provides `RCX` and `RDX` pointers, fills `R8D` with the exact version-dependent constant, and reads `R9D` from a global. The machine code immediately preceding includes `sete al` and writes a stack byte. It checks `EAX` after the imported BEE call and conditionally branches upon a nonzero result.

These observations indicate an explicit internal initialisation contract rather than an incidental function reference. **The meanings of the constants, the pointer arguments, the map content, and the flag remain unverified.** Do not call the constants an SDK version, layer type, plugin identifier, registry descriptor, or private extension ABI without additional evidence.

## Why it matters

The actual cross-module chain now extends through argument preparation:

```text
aelib.dll native initializer
  -> prepare pointer arguments + build-specific constant + state/flag
  -> imported BEE_Birth [result checked]
  -> BEE common registration helper
  -> built-in native BEE Layer/AV/Text/Vector RegisterStreams
```

The dual code paths do not establish two runtime startup executions. There is no evidence here that the argument map allows a third-party native layer class factory to be installed. An independent ChapeLayer still requires an explicit safe external constructor/registration and native owner/editor/render/serialization/unload contract. The public AEGP SDK inspection F-VECTOR-072 did not provide it.

## Evidence and tests

- `experiments/vector-shape/probe-src/tools/verify_aelib_bee_birth_argument_gates.py`
- `datasets/ae-aelib-bee-birth-argument-gates-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-075-bee-birth-argument-boundary.md`
- `experiments/observatory/manifests/EXP-SHAPE-075.json`

Verifier checks exact instruction-boundary setup patterns and return check for both native callsites in each installed version; **4/4 callsite checks PASS**. The dataset includes only small relevant bounded instruction excerpts and local file SHA-256, not complete Adobe executable code.

No Adobe executable/private routine was invoked, modified or injected, and no AEX GUI/user projects or CompNodeAE files were touched.

## Next high-value research

Reconstruct `RCX` string and `RDX` map production using the actual native call graph, rather than relying on names. Evaluate whether those objects carry configuration only or any genuinely extensible creator/provider contract. Keep the hypothesis open until a reproducible external registration example or a well-scoped negative census is available.
