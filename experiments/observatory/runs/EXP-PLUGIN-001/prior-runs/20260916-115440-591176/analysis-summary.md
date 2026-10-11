# EXP-PLUGIN-001 analysis

- Rows parsed: **3072**
- Successful acquisitions: **294**
- Published 25.6 selectors that failed: **6**
- Successful selectors not published in the 25.6 version table: **18**
- Suite families missing from the log: **0**
- Host version fields observed: `[('126', '3')]`

## Interpretation rules

A successful non-25.6 selector is a runtime observation, not automatically a supported public API; it may be a newer public generation, compatibility alias, or internal/host-specific table.
A published selector failure must be interpreted in host context: some suites are context/host scoped and may not be available to an Artisan AEGP entry point.
Pointer equality across successful selectors does not establish ABI equivalence; table layout remains version-specific unless separately proven.

## Published selectors that failed

- `AEGPCanvasSuite` selector 4 err=1394689636
- `AEGPCanvasSuite` selector 6 err=1394689636
- `AEGPRenderQueueMonitorSuite` selector 1 err=1394689636
- `AEGPCanvasSuite` selector 4 err=1394689636
- `AEGPCanvasSuite` selector 6 err=1394689636
- `AEGPRenderQueueMonitorSuite` selector 1 err=1394689636

## Unexpected successful selectors

- `AEGPArtisanUtilSuite` selector 2 ptr=00007FFAB430C590
- `AEGPCompSuite` selector 27 ptr=00007FFAB430D520
- `AEGPGuideSuite` selector 1 ptr=00007FFAB4356820
- `AEGPGuideSuite` selector 2 ptr=00007FFAB4356870
- `AEGPItemViewSuite` selector 2 ptr=00007FFAB43115B0
- `AEGPRegisterSuite` selector 7 ptr=00007FFAB43154D0
- `AEGPRegisterSuite` selector 8 ptr=00007FFAB4315530
- `AEGPSoundDataSuite` selector 1 ptr=00007FFAB430B808
- `AEGPTextLayerSuite` selector 2 ptr=00007FFAB43173D0
- `AEGPArtisanUtilSuite` selector 2 ptr=00007FFAB434C590
- `AEGPCompSuite` selector 27 ptr=00007FFAB434D520
- `AEGPGuideSuite` selector 1 ptr=00007FFAB4396820
- `AEGPGuideSuite` selector 2 ptr=00007FFAB4396870
- `AEGPItemViewSuite` selector 2 ptr=00007FFAB43515B0
- `AEGPRegisterSuite` selector 7 ptr=00007FFAB43554D0
- `AEGPRegisterSuite` selector 8 ptr=00007FFAB4355530
- `AEGPSoundDataSuite` selector 1 ptr=00007FFAB434B808
- `AEGPTextLayerSuite` selector 2 ptr=00007FFAB43573D0
