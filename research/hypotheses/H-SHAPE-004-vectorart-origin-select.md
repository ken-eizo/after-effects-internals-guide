---
status: hypothesis
last_verified: 2026-10-11
evidence: H + E2-L + E0-H
versions: AE 2025 / 2026 BEE.dll and AEGP Suite 6
---
# H-SHAPE-004 — Native path selection and evaluated geometry share a stream-path identity substrate

## Claim candidate

`BEE_VectorArt::OriginInfo` stores both direct and synthetic `TDB_StreamIDPath` references. Native selection contains `BEE_GetSelectedShapePathsVec` and `BEE_SelLayer::IsPathOrChildSelected(TDB_StreamIDPath const&)`. The conceptual possibility: an evaluated path could be reconnected to its editable timeline property by preserved origin IDs, including synthetic descendants.

## Necessary evidence before promotion

1. Static callers/consumers of OriginInfo path accessors, selection functions and display list rendering.
2. A controlled test recording the public `AEGP_GetUniqueStreamID` before and after native editing, child reorder and a repeater operation (does it preserve identity?).
3. Host traces of Pen tool selection and vertex editing with same path before/after.
4. Confirmation of any bridge between an externally created geometry object and registered editable stream; absent this, private OriginInfo construction cannot satisfy the user target.

Distinct hypotheses: native provenance-to-selection link, stable UID mapping, and third-party edit target registration. Do not conflate.
