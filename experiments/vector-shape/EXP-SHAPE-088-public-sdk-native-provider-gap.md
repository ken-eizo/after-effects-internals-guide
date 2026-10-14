# EXP-SHAPE-088 — Installed Adobe SDK public native Stream registrar audit

**PASS absence audit, scoped ONLY to installed SDK25.6's 70 public headers.**

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_public_sdk_native_provider_gap.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_native_host_product_gates.py"
```

`AEGP_RegisterSuite5` exposes 12 callbacks, none for native Stream/Layer class registration. `AEGP_DynamicStreamSuite4` exposes 26 methods including AEGP_AddStream and CanAddStream for **already registered** children. The headers contain no TDB_StreamBase, TDB_StreamFactory, BEE_Layer or custom Stream creator API. Latest 26.5 SDK release notes add Guides, parametric mesh layer creation and StreamSuite7 render-stage control, not a custom native type provider.

Status of EXACT user-requested native host Timeline deliverable:
`NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`.

Evidence: `datasets/ae25_6_public_native_stream_provider_api_scope_audit.json`, `datasets/chape_host_native_timeline_product_gate_20261014.json`. Scope is not a universal impossibility proof: private/partner SDKs or future host versions may permit it. Do not fake completion with private injection or a mock CNL-owned property tree. See F-VECTOR-088.
