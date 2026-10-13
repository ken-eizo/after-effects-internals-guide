---
date: 2026-10-13
status: patch compiled 2/2 CTest PASS, PE PASS; host rerun needed
evidence: E2-X user screenshot and TEMP TSV, E2-L public SDK grouping enum and patched AEX static build
---
# EXP-SHAPE-064 — ChapeLayer native indexed group misuse and menu visibility investigation

The user saw a native AE2026 assertion "GetNewStreamRefByMatchname only works on named groups" followed by a ChapeLayer probe report. Its TEMP TSV proves ADBE Root Vectors Group has grouping type INDEXED_GROUP (=2), not a named group, and the root layer stream is NAMED_GROUP (=1).

Fixed ChapeHostAdmissionProbe.cpp with grouping-type guard before any by-MatchName call, using Root Vectors as Contents itself, child traversal via by-INDEX API, nested Group Contents only behind named child and unique dispose. Fixed native startup registers ChapeLayer at public AEGP_Menu_NEW TOP and an additional AEGP_Menu_LAYER TOP fallback while logging all results into TEMP/ChapeLayer_MenuRegistration.tsv.

No AE native owner type is created (both menu commands fail-closed). Built AEX now outputs a TSV for inspection, only in a manual user-host run. AEGP_Menu_NEW availability in SDK is documented, but visible rendering is not confirmed by the prior screenshot; new host test pending.

Rebuilt in active D:/Developer/ShapeLayerAE; CTest 2/2 PASS, PE static checks passed. No user project, AE GUI or private host registrar touched. This new build was never installed/tested by assistant.
Research: F-VECTOR-064.
