// Original CompNodeAE vector geometry PICA suite (research protocol v1).
// Non-raster, layer-local native numeric cubics; NOT Adobe VectorArt.
#pragma once
#include "A.h"
#include "SPTypes.h"
#include <cstdint>
#define kCNLVectorBridgeSuite1 "CompNodeAE Vector Geometry Suite"
#define kCNLVectorBridgeSuiteVersion1 1
struct CNL_VectorCubicV1 {double x0,y0,x1,y1,x2,y2,x3,y3;};
struct CNL_VectorPathInfoV1 {uint32_t byte_size,cubic_count,closed,geometry_revision;};
typedef struct CNL_VectorBridgeSuite1 {
 SPAPI A_Err (*DescribePath)(uint32_t,CNL_VectorPathInfoV1*);
 SPAPI A_Err (*CopyCubicPath)(uint32_t,int64_t,int64_t,CNL_VectorCubicV1*,uint32_t,uint32_t*);
} CNL_VectorBridgeSuite1;
static_assert(sizeof(CNL_VectorCubicV1)==64,"Cross-DLL ABI size mismatch");
