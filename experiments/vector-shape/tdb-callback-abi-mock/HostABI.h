// Model of private MSVC erased callback signature, NOT Adobe headers or ABI.
#pragma once
#include <functional>
#include <stdint.h>
#include <stddef.h>
#ifdef HOST_MOCK_EXPORTS
#define MOCK_API __declspec(dllexport)
#else
#define MOCK_API __declspec(dllimport)
#endif
struct MatchNameLike {
 uint64_t guid_a;
 uint64_t guid_b;
};
static_assert(sizeof(MatchNameLike)==16, "TDB_MatchName writes a 16-byte GUID");
struct StreamLike {
 virtual ~StreamLike()=default;
 virtual bool IsLeaf() const=0;
 virtual StreamLike* GetAsLeaf()=0;
 virtual void SetupCanonicalLayout()=0;
};
using NativeCreatorLike=std::function<StreamLike*(const MatchNameLike&,void*,bool,unsigned,bool)>;
// Deliberately pass std::function by VALUE across an EXE/DLL boundary
// and keep it beyond the lifetime of the originating parameter.
extern "C" {
MOCK_API bool MockRegister(const MatchNameLike&,NativeCreatorLike,bool);
MOCK_API bool MockUnregister(const MatchNameLike&);
MOCK_API bool MockIsRegistered(const MatchNameLike&);
MOCK_API bool MockHasCanonical(const MatchNameLike&);
MOCK_API size_t MockCount(void);
MOCK_API int MockCanonicalLayoutCalls(void);
MOCK_API int MockStreamDestructors(void);
}
