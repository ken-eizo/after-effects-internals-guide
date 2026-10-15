---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L
scope: Windows 10 / CPU passthrough benchmark on user's machine
confidence: high for standalone copy latency; not a measured AE render path
---
# F-UI-010 - Identity effect copies can dwarf manipulator math

## Scoped statement

An effect implementing native custom Composition UI can have an
extremely cheap manipulator state model while its separate
PF_Cmd_RENDER image passthrough copies enough pixels that a
universal 0.01 ms cap for all operations is unrealistic on the
measured hardware. This distinction matters when profiling the
performance of an otherwise UI-only diagnostic effect.

GizmoInputProbe has a sample passthrough implementation
that copies input layer rows to output layer rows with memmove.
The transfer is per rendered pixel, unrelated to the
animated gizmo's six node coordinates.

## Measured CPU memory-transfer baseline

Command:
D:/Developer/GizmoSearchAE/build-ae/Release/GizmoCopyBench.exe

Release standalone memcpy benchmark on the user's Windows PC:

| RGBA8 frame | Data copied | Median CPU copy |
| --- | ---: | ---: |
| 1280x720 | 3.52 MiB | 170.30 microseconds |
| 1920x1080 | 7.91 MiB | 341.50 microseconds |
| 3840x2160 | 31.64 MiB | 2793.40 microseconds |

The measurement uses one contiguous CPU memcpy per frame and
samples a different data byte after each copy. Actual AE may use
row strides, different pixel depth, different memory/pool policy,
native copy optimizations, render caches, or GPU paths; these
numbers are NOT recorded AE PF_Cmd_RENDER timings.

The required memory bandwidth grows linearly with frame
area and bytes per pixel. Pixel transfers also read a source
and write a destination, making the operation memory-bandwidth
bound when buffers exceed cache.

## Architectural consequence

For other production plug-ins reusing GizmoKit, do NOT add
GizmoInputProbe.aex simply to obtain a gizmo. Integrate the
model and host adapter into the effect that already owns the
required parameter/render state, so the extra diagnostic
effect does not add a separate image-processing pass.

Reducing source-level arithmetic or substituting Vulkan
for the few control-point calculations cannot eliminate an
effect instance's mandatory host image output semantics.
A genuine zero-copy identity adapter would require a
documented host-supported path and version-specific
evidence; it must not be invented by omitting PF_Cmd_RENDER.

The distinction is general: optimize the editor overlay
pipeline and the image-processing graph independently,
report their memory and compute costs separately, and
do not attribute an image-copy ceiling to Drawbot geometry.
