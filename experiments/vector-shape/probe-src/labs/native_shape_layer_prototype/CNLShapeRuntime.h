// CNL native vector-owner runtime. Its objects are independently owned by CNL.
// It is NOT an Adobe BEE/TDB object and does NOT appear as a native AE Layer yet.
#pragma once
#include "../native_vector_core/CNLNativeVectorCore.h"
#ifdef _WIN32
# define CNL_SHAPE_API __declspec(dllexport)
#else
# define CNL_SHAPE_API
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef struct CNL_ShapeLayer CNL_ShapeLayer;
typedef struct CNL_ShapeFeatures {
    uint32_t abi_version;
    uint32_t supports_editable_cubics;
    uint32_t supports_nested_contents;
    uint32_t supports_stable_archive;
    uint32_t supports_undo_redo;
    uint32_t supports_vector_svg;
    uint32_t connected_to_adobe_native_tdb;
    uint32_t connected_to_adobe_contents;
    uint32_t connected_to_adobe_pen;
    uint32_t connected_to_adobe_vectorart;
} CNL_ShapeFeatures;
CNL_SHAPE_API CNL_ShapeFeatures cnl_shape_features(void);
CNL_SHAPE_API CNL_ShapeLayer* cnl_shape_create(void);
CNL_SHAPE_API void cnl_shape_destroy(CNL_ShapeLayer* shape);
CNL_SHAPE_API CNL_NodeId cnl_shape_contents_root(const CNL_ShapeLayer* shape);
CNL_SHAPE_API CNL_Status cnl_shape_add_group(CNL_ShapeLayer* shape,CNL_NodeId parent,const char* name,CNL_NodeId* id);
CNL_SHAPE_API CNL_Status cnl_shape_add_path(CNL_ShapeLayer* shape,CNL_NodeId parent,const char* name,int closed,const CNL_PathVertex* points,uint32_t count,CNL_NodeId* id);
CNL_SHAPE_API CNL_Status cnl_shape_add_ellipse(CNL_ShapeLayer* shape,CNL_NodeId parent,const char* name,double x,double y,double rx,double ry,CNL_NodeId* id);
CNL_SHAPE_API CNL_Status cnl_shape_set_vertex(CNL_ShapeLayer* shape,CNL_NodeId path,uint32_t index,const CNL_PathVertex* value);
CNL_SHAPE_API CNL_Status cnl_shape_move_node(CNL_ShapeLayer* shape,CNL_NodeId node,CNL_NodeId parent);
CNL_SHAPE_API CNL_Status cnl_shape_get_vertex(const CNL_ShapeLayer* shape,CNL_NodeId path,uint32_t index,CNL_PathVertex* out);
CNL_SHAPE_API uint32_t cnl_shape_undo_depth(const CNL_ShapeLayer* shape);
CNL_SHAPE_API uint32_t cnl_shape_redo_depth(const CNL_ShapeLayer* shape);
CNL_SHAPE_API CNL_Status cnl_shape_undo(CNL_ShapeLayer* shape);
CNL_SHAPE_API CNL_Status cnl_shape_redo(CNL_ShapeLayer* shape);
CNL_SHAPE_API CNL_Status cnl_shape_archive(const CNL_ShapeLayer* shape,void* dest,size_t* count);
CNL_SHAPE_API CNL_Status cnl_shape_from_archive(const void* data,size_t count,CNL_ShapeLayer** out);
CNL_SHAPE_API CNL_Status cnl_shape_svg(const CNL_ShapeLayer* shape,char* dest,size_t* count);
#ifdef __cplusplus
}
#endif
