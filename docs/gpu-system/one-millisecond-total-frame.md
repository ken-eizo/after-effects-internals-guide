---
status: experimental-performance-target-not-demonstrated-in-actual-adobe-ae
last_verified: 2026-10-14
evidence:
  - Official Adobe Composition Profiler documentation
  - RTX 2070 SUPER official 448 GB/s GDDR6 specification
  - SDK-shaped physical Windows D3D12 GPU experiments, not actual Adobe AE host
---
# 1 ms TOTAL FRAME: host-visible Composition Profiler performance gate

**The metric is Adobe After Effects Timeline footer "Frame Render Time", not:**
- GPU shader timestamp, hardware kernel latency, D3D12 callback p50/p95, AEX selector duration, or independent benchmark time.
- Per-effect / per-layer "Render Time" column, which can have a different numerator.
- Cached timeline playback rate, preview frame rate, or disk-cache file writing time.

The Adobe Composition Profiler footer reports the whole currently rendered composition frame. The Render Time column can drill down to layers and effects. Cached values may carry an asterisk and include cache retrieval; purge/fully re-rendering is necessary for a cold source truth. Full vs Half viewer resolution, Adaptive Resolution, ROI, bit depth and current render frame affect interpretation.
Official primary source: https://helpx.adobe.com/after-effects/desktop/work-with-compositions/composition-profiler/composition-profiler.html (2026-04-30).

## Non-negotiable mathematical limits

For 32bpc RGBA with a full-frame 16-byte input read and a full-frame 16-byte output write (no intermediates), the MINIMUM external VRAM traffic is 32 bytes/pixel:
| Format | Pixels | Minimum traffic | Ideal lower bound @ 448 GB/s |
| --- | ---: | ---: | ---: |
| HD 1920x1080 | 2,073,600 | 66.36 MB | 0.148 ms |
| UHD 3840x2160 | 8,294,400 | 265.42 MB | 0.592 ms |
| 8K 7680x4320 | 33,177,600 | 1,061.68 MB | 2.370 ms |

Source for exact card bandwidth: https://www.nvidia.com/content/nvidiaGDC/gb/en_GB/geforce/graphics-cards/rtx-2070-super.html (RTX 2070 SUPER memory bandwidth 448 GB/s). These times are **optimistic theoretical memory-traffic lower bounds**, not measured timings. They exclude actual bandwidth loss, shader compute, dispatch, AE scheduling/cache, GPU fences, memory uploads, host compositing, additional layers and intermediate frames. CPU caches may change where actual bytes reside. At 8K on this hardware, even this simple mandatory read+write exceeds 1 ms. Therefore a universal all-workloads <1ms requirement is physically impossible.

## API and ownership optimizations that are safe to adopt

1. Honor Adobe SmartFX ROI: request only needed input and intersect result_rect with the requested output. **max_result_rect must depend on actual source bounds, NOT the current ROI**. The latest corrected C++ preRender now uses the source's checkout max_result_rect; tests vary the output ROI to catch violations. Content bounds for alpha-preserving operations are the source bounds; expansion operators must derive larger accurate max bounds.
2. Make full math fusion the default for image operations whenever output numerical semantics (HDR, alpha, NaN, precision) are preserved. Minimize full-frame intermediates and GPU resident<->CPU conversions.
3. Windows D3D12 and Mac Metal should remain supported native AE host backends. Pixel kernels may be conditionally tuned per host/hardware, but only when end-to-end actual-host frame speed is measured.
4. Pre-build pipelines once per device; lease request-exclusive allocator/list and fence-lifetime resources under MFR. Cache misses, excess contexts and GPU queue waits should be measured separately. "GPU completion" cannot be assumed before checkin unless the actual host's device/queue contract proves it; an unsafe async return is not a valid "optimization."
5. Keep CPU SIMD as correctness and low-end fallback; a GPU-only plugin would violate compatibility/stability on unsupported hardware.
6. Never treat synthetic GPU World shareability as proof that real Adobe-owned GPU Worlds can be exported to Vulkan. Preserve the original 7-step host interop admission gate.
7. Cache efficacy belongs to the **host's** whole-frame evaluation. Plugins can reduce dependencies and preserve stable cache keys/ROI; they cannot guarantee a timeline frame's render time independently of all layers and source effects.

## Verified isolated measurements versus missing Adobe measurements

As of this revision, the actual AE Timeline footer was **not captured or benchmarked**. Normal user AE2026 remained running, and authorized offline test work did not install any research AEX in its registered plugin scanner path. The Windows compiled AEX and physical RTX2070 SUPER were measured with SDK-shaped fake AE callbacks and GPU-owned DEFAULT heap Worlds, with full fence waits. The 3 GPU tilings use identical HLSL pixel math, and real GPU pixel parity is checked on 1919x1079 padded row stride, 1920x1080 and 3840x2160.

Raw randomized benchmark (45 independently launched GPU mock processes, 48 callbacks each, 3 tilings × 3 sizes × 5 repeats): D:/Developer/AEEffectPerformanceLab/results/native-d3d12-threadgroup-ab-sdk-roi-20261014.json. It reports mock callback wall-time p50/p95 only, **NOT Adobe Frame Render Time**, and includes each SHA-256-scoped AEX binary. The 16x16 default is retained in production-oriented code because alternate mappings have not been tested in actual AE.

The CPU AVX2 synthetic host at 1920x1080 measured 48 callback p50=7.768 ms, p95=10.669 ms; 3840x2160 p50=29.548ms, p95=44.061ms (one run each, host synthetic, October 14). The real GPU callback examples are substantially faster in this research fixture, but do **not** imply that the AE frame footer equals the GPU callback time.

## Required actual Adobe AE profiler protocol

1. **Disposable, correctly registered AE 2026 host:** confirm AEX scanned/loaded with PID, specific AfterFX.exe full path, AE build, exact AEX checksum, app-version and driver/CPU/GPU model. The active user's open AE2026 project must not be modified.
2. **Test fixture**: empty, disposable AE project created under isolated test host, 32bpc, no external footage, 1920x1080 and 3840x2160 and at least one padding/ROI case; a synthetic image on one layer with single target effect. Then separately test multi-layer and real media workloads. A solid color may allow special caching paths; do not use only a constant still.
3. **Cold-cache Frame Render Time**: enable Composition Profiler (snail icon/Render Time column). Full resolution, Adaptive Resolution OFF, stable zoom, motion blur/frame blending consistent, GPU/render settings noted. Purge All Memory and Disk Cache before truly cold measurements. A cached result with '*' does not count as a full recompute. Do not purge the user's normal AE cache; only on the disposable profile. Collect visible footer values and layer/effect breakdown for different actual frames.
4. **Fixture identity and replication**: log layer stack/effects, ROI, 8/16/32bpc, motion blur, color management, GPU device, GPU/CPU rendering choice, MFR worker count (1/2/4/8), caching state, number of unique frames. Record ≥120 **distinct un-cached full-frame outcomes** per candidate/hardware/resolution/operation; p50/p95/p99 and MAX, with screenshot or verifiable numeric extraction of the Adobe UI. UI-only footer timing is not interchangeable with scripted save-to-PNG wall time or aerender output time.
5. **Hard acceptance**: a candidate may claim the narrowly scoped sub-1ms *observed* target only if actual-Adobe, uncached total Frame Render Time p95, p99, AND MAX are each <1ms for at least 120 distinct frames and correct pixels, with all tested memory/driver/cancellation safety gates green. It still does NOT guarantee future frames under any conditions. Missing samples, cached values, 1ms+ outliers, synthetic mock data, per-layer-only values and kernel-only timestamps must FAIL CLOSED.
6. **A/B selection**: use same source frame sequence, precision, view resolution, ambient load and device; use randomized baseline/candidate alternation to avoid heat/cache biases. Evaluate low-end RAM/VRAM and native Mac separately. Never compare p95 between unlike fixtures as a speed ranking.
7. **Diagnostic**: If footer >1ms, expand per-effect Render Time and compare with no-effect baseline. If effect itself <1ms but full frame >1ms, optimize source and AE cache/renderer separately. The SDK cannot change the host's unrelated layer compute time.

## Machine-readable enforcement

Source: D:/Developer/AEEffectPerformanceLab/core/effect_core.hpp and effect_core.cpp. The function eligible_sub_ms_ae_frame_candidates() requires:
- actual-host eligible production candidate and same full benchmark fixture,
- TimingScope::AECompositionFrameProfiler,
- CacheMeasurement::FullyUncached,
- frameSamples >= 120,
- finite, ordered p95, p99, maximumObservedMilliseconds all <1.0,
- correct parity, stability, bounded memory, residency transfers and sanctioned host GPU API as in existing production gate.

The simulated unit tests assert that even an excellent 0.1ms mock shader cannot be promoted. The actual-host performance admission set is currently **EMPTY** because the Adobe Timeline Frame Render Time has not been measured.

The research objective remains **highest possible real-AE stability and end-to-end performance**, not arbitrary promises of 1ms for workloads that need many milliseconds of memory or arithmetic. All source and measurements must be reproducible and their uncertainty explicit.
