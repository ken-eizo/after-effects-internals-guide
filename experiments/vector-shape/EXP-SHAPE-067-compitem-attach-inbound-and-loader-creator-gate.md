---
date: 2026-10-14
status: PASS native cross-version direct incoming attach xrefs, factory ordering in 4 load functions
evidence: E2-L installed BEE2025/BEE2026 static x64 instructions
---
# EXP-SHAPE-067 — CompItem native owner insertion alternative route census

We enumerated incoming x64 direct relative CALLs into:
- native CompItem AttachLayerToCompOnly, 2025 0x392120 / 2026 0x39D4D0.
- native CompItem AttachLayerToCompAndLayerParamsOnly,
  2025 0x3920F0 / 2026 0x39D4A0.

11 exact direct caller instruction sites and 10 unique caller functions
in EACH binary. Verified relative call targets against decoded Capstone
native instruction addresses and PE pdata function ranges.

Native BEE_Layer::CloneAndAttach is among the callers, as is
BEE_TextLayer::CloneAndAttachFromAVLayer and the normal new-layer worker.
This does not by itself provide a foreign owner class factory.

Most important: the two primary project/file materializer functions on
each platform do NOT sidestep the 0..7 native LayerType switch.
2025 0x505090 / 0x505400 both call CreateLayerFromType RVA 0x2E3E10
BEFORE direct CompItem attach RVA 0x392120.
2026 0x51F2F0 / 0x51F650 both call CreateLayerFromType RVA 0x2ECD00
BEFORE direct CompItem attach RVA 0x39D4D0.
Actual callsite RVAs in F-VECTOR-067.

Verifier PASSED AE2025/2026. CompItem's generic attach accepts a
native BEE_Layer pointer, but safe creation/ownership of a foreign class
is still unproven. No external plugin registration or host
native subclass was created, no private function executed. No vendor
binary modified or redistributed.

Next feasibility gate: alternative host-admitted foreign BEE_Layer
constructor and correctly owned TDB canonical/Undo/evaluator/editor state.
The current CNL typed native Timeline C ABI F-VECTOR-066 remains a CNL
runtime only; it is NOT native Adobe Contents or Layer integration.
