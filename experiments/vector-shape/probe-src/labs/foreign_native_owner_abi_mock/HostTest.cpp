// Isolated cross-DLL model of Clone -> RTTI BEE Layer -> Comp ownership.
// Strictly NOT an AE-host integration test; no Adobe API is loaded or invoked.
#include "MockHostABI.h"
#include <Windows.h>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <vector>
#define CHECK(x) do {if(!(x)){std::fprintf(stderr,"FAIL %s line %d\n",#x,__LINE__);return 2;}}while(0)
struct MockComp {
 std::vector<std::unique_ptr<MockBEE_Layer>> owned;
 bool cloneAndAttach(const MockTDB_StreamBase& source){
  std::unique_ptr<MockTDB_StreamBase> clone(source.clone());
  if(!clone)return false;
  auto* cast=dynamic_cast<MockBEE_Layer*>(clone.get());
  if(!cast)return false; // foreign TDB Stream is not a BEE Layer
  // Transfer the cloned object's ownership, not the original object.
  clone.release();
  owned.emplace_back(cast);
  return true;
 }
};
template<class T>
T proc(HMODULE module,const char* name){
 return reinterpret_cast<T>(GetProcAddress(module,name));
}
using Version=std::uint32_t(*)();
using Create=MockTDB_StreamBase*(*)(std::uint64_t);
using CreateForeign=MockTDB_StreamBase*(*)();
using Live=int(*)();
int main(int argc,char** argv){
 CHECK(argc==2);
 HMODULE module=LoadLibraryA(argv[1]);
 CHECK(module!=nullptr);
 const auto version=proc<Version>(module,"chape_mock_abi_version");
 const auto create=proc<Create>(module,"chape_mock_create_layer");
 const auto foreign=proc<CreateForeign>(module,"chape_mock_create_nonlayer");
 const auto count=proc<Live>(module,"chape_mock_live_objects");
 CHECK(version && create && foreign && count);
 CHECK(version()==CHAPE_MOCK_ABI_VERSION);
 CHECK(count()==0);
 {
  std::unique_ptr<MockTDB_StreamBase> layer(create(0x123456789ULL));
  CHECK(layer!=nullptr);
  CHECK(layer->typeId()==42);
  auto* base=dynamic_cast<MockBEE_Layer*>(layer.get());
  CHECK(base!=nullptr && base->stableId()==0x123456789ULL);
  CHECK(count()==1);
  MockComp comp;
  CHECK(comp.cloneAndAttach(*layer));
  CHECK(count()==2);
  CHECK(comp.owned.size()==1);
  CHECK(comp.owned[0].get()!=base);
  CHECK(comp.owned[0]->stableId()==base->stableId());
  {
   std::unique_ptr<MockTDB_StreamBase> other(foreign());
   CHECK(other && other->typeId()==9001);
   CHECK(dynamic_cast<MockBEE_Layer*>(other.get())==nullptr);
   CHECK(!comp.cloneAndAttach(*other));
   CHECK(comp.owned.size()==1);
   CHECK(count()==3);
  }
  CHECK(count()==2);
  // A real loader MUST refuse unload while either source/clone exists:
  CHECK(count()>0);
  // Do not call FreeLibrary here; the live plugin class vtable would dangle.
  comp.owned.clear();
  CHECK(count()==1);
  layer.reset();
  CHECK(count()==0);
 }
 CHECK(count()==0);
 CHECK(FreeLibrary(module)!=0);
 std::puts("PASS cross-DLL shared RTTI, polymorphic TDB clone, BEE Layer dynamic_cast, Comp ownership and unload lifetime. MOCK ONLY; Adobe native layer registration NOT proven.");
 return 0;
}
