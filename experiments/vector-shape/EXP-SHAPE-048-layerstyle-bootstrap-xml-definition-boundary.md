---
status: pass-cross-version-static
date: 2026-10-12
evidence: E2-L
---
# EXP-SHAPE-048 — Layer Style XML parser startup/teardown argument provenance

Inspect true BEE2025/26 executable relative calls/jumps to XML/parser initializer, follow native wrapper and bootstrap callsites two hops, and assert that `RCX` definition argument is forwarded to the XML parser initializer's `RDX`. In both versions, its local string is passed to the parser object virtual `+0x18` method. Separate teardown wrapper passes `ECX=0/EDX=0`, invoking the unregister branch of the same initializer, alongside BEE's larger shutdown routine.

Cross-version machine-code verifier `verify_layerstyle_xml_scope_lifecycle.py`: PASS. This does not prove external XML file provenance or supported third-party registration; it is an internal native startup/teardown boundary. No AE host invocation or mutation. See F-VECTOR-048.
