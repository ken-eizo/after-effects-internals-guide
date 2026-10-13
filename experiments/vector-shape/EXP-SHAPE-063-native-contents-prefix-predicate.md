---
date: 2026-10-13
status: PASS on-disk AE2025 and AE2026 BEE.dll executable code + in-host AEGP CanAdd correlation
evidence: E2-L BEE native CanStore, CRT import thunk and three literal references; E2-X user's 2026 TSV
---
# EXP-SHAPE-063 — Full native Shape parent-match admission code reconstructed

Disassembled installed 2025 BEE_VectorStream::VectorsStreamGroup::CanStore at 0x700250 and installed 2026 at 0x723C80. Recovered one special exact TDB_MatchName comparison followed by three calls to VCRUNTIME140.dll!strstr with native MatchName::GetName as haystack, literals "ADBE Vector Shape -", "ADBE Vector Graphic -" and "ADBE Vector Filter -" as needle. Native CMP RAX,RBX validates returned pointer equals the original string start, proving a prefix test (not generic substring search). No direct TDB factory/CanCreate query or BEE evaluator lookup exists in this predicate.

Verified AE2025 0xCEACFE and AE2026 0xD3BE2E shared search thunk patterns; 2026 IAT RVA 0xF19510 is the actual VCRUNTIME140.dll strstr import (confirmed by installed dumpbin /imports). Both executable-code shape checks PASS.

In the user's earlier real AE2026 TSV, unknown ADBE-prefixed types yield CanAdd=TRUE and CNL:Path yields FALSE. No native factory instantiation was attempted.

The exact identity of the initial special-case TDB_MatchName constant is not yet resolved. The three prefix clauses and no factory check are the supported conclusion. The result is a **parent acceptance contract** and absolutely not permission to create arbitrary new stream types in stock AE.

Scripts: experiments/vector-shape/probe-src/tools/verify_native_contents_prefix_canstore_full.py
Dataset: datasets/ae-vector-contents-canstore-full-predicate-2025-2026.json
Research: F-VECTOR-063. No AE process operation, private registry call or binary modification.
