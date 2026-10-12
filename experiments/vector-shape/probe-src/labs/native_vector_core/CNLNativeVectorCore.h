// CompNodeAE independently owned path/Contents document core.
// NOT Adobe TDB ABI, NOT a Mask/Shape Layer, NOT PF_World output.
#pragma once
#include <stdint.h>
#include <stddef.h>
#ifdef _WIN32
# ifdef CNL_VECTOR_CORE_EXPORTS
#  define CNL_EXPORT __declspec(dllexport)
# else
#  define CNL_EXPORT __declspec(dllimport)
# endif
#else
# define CNL_EXPORT
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef struct CNL_Document CNL_Document;
typedef uint64_t CNL_NodeId;
typedef struct CNL_PathVertex {
    double x,y,in_dx,in_dy,out_dx,out_dy;
} CNL_PathVertex;
typedef struct CNL_CubicBezier {
    double x0,y0,x1,y1,x2,y2,x3,y3;
} CNL_CubicBezier;
typedef enum CNL_Status {
    CNL_OK=0,CNL_INVALID_ARGUMENT=1,CNL_NOT_FOUND=2,CNL_WRONG_TYPE=3,
    CNL_OUT_OF_RANGE=4,CNL_NO_SPACE=5,CNL_BAD_ARCHIVE=6,
    CNL_UNSUPPORTED_ARCHIVE_VERSION=7,CNL_CYCLE=8,CNL_LIMIT_EXCEEDED=9,
    CNL_INTERNAL_ERROR=10
} CNL_Status;
typedef enum CNL_NodeKind {CNL_NODE_GROUP=1,CNL_NODE_PATH=2} CNL_NodeKind;
typedef struct CNL_CoreVersion {uint32_t abi_version, archive_version;} CNL_CoreVersion;
CNL_EXPORT CNL_CoreVersion cnl_core_version(void);
CNL_EXPORT CNL_Document* cnl_document_create(void);
CNL_EXPORT void cnl_document_destroy(CNL_Document*);
CNL_EXPORT CNL_Status cnl_document_clone(const CNL_Document*,CNL_Document**);
CNL_EXPORT CNL_NodeId cnl_document_root(const CNL_Document*);
CNL_EXPORT CNL_Status cnl_document_add_group(CNL_Document*,CNL_NodeId,const char* name,CNL_NodeId*);
CNL_EXPORT CNL_Status cnl_document_add_path(CNL_Document*,CNL_NodeId,const char* name,int closed,
    const CNL_PathVertex*,uint32_t count,CNL_NodeId*);
CNL_EXPORT CNL_Status cnl_document_add_ellipse(CNL_Document*,CNL_NodeId,const char* name,
    double center_x,double center_y,double radius_x,double radius_y,CNL_NodeId*);
CNL_EXPORT CNL_Status cnl_document_copy_cubics(const CNL_Document*,CNL_NodeId,
    CNL_CubicBezier* dest,uint32_t* count);
CNL_EXPORT CNL_Status cnl_document_move_node(CNL_Document*,CNL_NodeId,CNL_NodeId);
CNL_EXPORT CNL_Status cnl_document_get_kind(const CNL_Document*,CNL_NodeId,CNL_NodeKind*);
CNL_EXPORT CNL_Status cnl_document_get_parent(const CNL_Document*,CNL_NodeId,CNL_NodeId*);
CNL_EXPORT CNL_Status cnl_document_get_child_count(const CNL_Document*,CNL_NodeId,uint32_t*);
CNL_EXPORT CNL_Status cnl_document_get_child(const CNL_Document*,CNL_NodeId,uint32_t,CNL_NodeId*);
CNL_EXPORT CNL_Status cnl_document_get_name(const CNL_Document*,CNL_NodeId,char*,size_t* bytes);
CNL_EXPORT CNL_Status cnl_document_get_path_info(const CNL_Document*,CNL_NodeId,int* closed,uint32_t* count);
CNL_EXPORT CNL_Status cnl_document_get_vertex(const CNL_Document*,CNL_NodeId,uint32_t,CNL_PathVertex*);
CNL_EXPORT CNL_Status cnl_document_set_vertex(CNL_Document*,CNL_NodeId,uint32_t,const CNL_PathVertex*);
CNL_EXPORT CNL_Status cnl_document_serialize(const CNL_Document*,void*,size_t* bytes);
CNL_EXPORT CNL_Status cnl_document_deserialize(const void*,size_t,CNL_Document**);
#ifdef __cplusplus
}
#endif
