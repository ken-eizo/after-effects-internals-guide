#pragma once
// ChapeLayer C ABI v1: standalone typed native Timeline grammar.
// NOT Adobe TDB / BEE binary or an AE native Timeline registration API.
#include <stddef.h>
#include <stdint.h>
#ifdef _WIN32
#define CHAPE_TIMELINE_EXPORT __declspec(dllexport)
#else
#define CHAPE_TIMELINE_EXPORT
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef struct CHAPE_Timeline CHAPE_Timeline;
typedef struct CHAPE_Value { double components[4]; } CHAPE_Value;
typedef struct CHAPE_Key {
 int64_t tick;
 CHAPE_Value value;
 uint32_t interpolation; // 0 = hold, 1 = linear
} CHAPE_Key;
typedef struct CHAPE_EvalEvent {
 uint64_t node_id;
 uint32_t action; // 0=group begin, 1=typed property, 2=group end
 const char* matchName; // borrowed for callback duration only
 CHAPE_Value value;
} CHAPE_EvalEvent;
typedef enum CHAPE_Result {
 CHAPE_OK=0,
 CHAPE_MISSING=1,
 CHAPE_INVALID=2,
 CHAPE_UNKNOWN_TYPE=3,
 CHAPE_DUPLICATE=4,
 CHAPE_FORBIDDEN=5,
 CHAPE_WRONG_KIND=6,
 CHAPE_CYCLE=7,
 CHAPE_RANGE=8,
 CHAPE_LIMIT=9,
 CHAPE_CORRUPT=10,
 CHAPE_EMPTY_HISTORY=11,
 CHAPE_NO_SPACE=12,
 CHAPE_INTERNAL_ERROR=13
} CHAPE_Result;
CHAPE_TIMELINE_EXPORT uint32_t chape_timeline_abi_version(void);
CHAPE_TIMELINE_EXPORT CHAPE_Timeline* chape_timeline_create(void);
CHAPE_TIMELINE_EXPORT void chape_timeline_destroy(CHAPE_Timeline* timeline);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_define_type(CHAPE_Timeline* timeline,
 const char* matchName,uint32_t kind,uint32_t order);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_permit(CHAPE_Timeline* timeline,
 const char* parentType,const char* const* childTypes,size_t count);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_add(CHAPE_Timeline* timeline,
 uint64_t parent,const char* matchName,const char* label,uint64_t* newId);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_move(CHAPE_Timeline* timeline,
 uint64_t id,uint64_t newParent,size_t insertIndex);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_set_base(CHAPE_Timeline* timeline,uint64_t id,const CHAPE_Value* value);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_set_key(CHAPE_Timeline* timeline,uint64_t id,const CHAPE_Key* key);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_sample(const CHAPE_Timeline* timeline,
 uint64_t id,int64_t tick,CHAPE_Value* out);
typedef CHAPE_Result (*CHAPE_VisitEvent)(const CHAPE_EvalEvent*,void* user);
// Synchronous ordered visitor; no stored callbacks / no ownership of callback code.
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_evaluate(const CHAPE_Timeline* timeline,
 int64_t tick,CHAPE_VisitEvent visitor,void* user);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_archive(const CHAPE_Timeline* timeline,
 void* data,size_t* bytes);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_restore(const void* data,size_t bytes,
 CHAPE_Timeline** output);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_undo(CHAPE_Timeline* timeline);
CHAPE_TIMELINE_EXPORT CHAPE_Result chape_timeline_redo(CHAPE_Timeline* timeline);
#ifdef __cplusplus
}
#endif
