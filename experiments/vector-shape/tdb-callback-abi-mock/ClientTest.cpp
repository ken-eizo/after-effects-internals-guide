#include "HostABI.h"
#include <cassert>
#include <cstdio>
#include <memory>
#include <vector>
#include <string>
#include <functional>
#include <atomic>
#include <type_traits>
#define CHECK(c) do{if(!(c)){std::fprintf(stderr,"FAIL %s @%d\n",#c,__LINE__);return 2;}}while(0)
class NativeComplete final:public StreamLike{
public:
 static inline int created=0, destroyed=0, layouts=0;
 NativeComplete(){++created;}
 ~NativeComplete() override{++destroyed;}
 bool IsLeaf()const override{return true;}
 StreamLike* GetAsLeaf()override{return this;}
 void SetupCanonicalLayout()override{++layouts;}
};
static StreamLike* AdobeNativeCreatorLike(
 const MatchNameLike&,void*,bool,unsigned,unsigned) {
 return new NativeComplete();
}
int main() {
 static_assert(sizeof(void*)==8);
 const MatchNameLike k0{0x99,0xabcd}, k1{0x99,0xabce};
 CHECK(MockCount()==0);
 CHECK(!MockIsRegistered(k0));
 CHECK(MockRegister(k0,AdobeNativeCreatorLike,true));
 CHECK(MockIsRegistered(k0));
 CHECK(MockHasCanonical(k0));
 CHECK(NativeComplete::created==1); // callback invoked before Register returned
 CHECK(NativeComplete::layouts==1);
 CHECK(MockCanonicalLayoutCalls()==1);
 CHECK(!MockRegister(k0,AdobeNativeCreatorLike,false)); // duplicates rejected
 CHECK(MockCount()==1);
 auto lifetime=std::make_shared<int>(7);
 std::weak_ptr<int> observed=lifetime;
 bool registered=false;
 {
  // Proves standard MSVC std::function captures retain the calling module
  // and must NOT remain in a native host registry after a plugin unload.
  auto creator=[token=lifetime](const MatchNameLike&,void*,bool,unsigned,unsigned)->StreamLike*{
   return new NativeComplete();
  };
  registered=MockRegister(k1,creator,false);
 }
 CHECK(registered);
 CHECK(NativeComplete::created==2);
 CHECK(MockCount()==2);
 lifetime.reset();
 CHECK(!observed.expired()); // native 'host' holds the copied callable
 std::vector<MatchNameLike> reverse{k0,k1};
 for(auto it=reverse.rbegin();it!=reverse.rend();++it){
  CHECK(MockUnregister(*it));
  CHECK(!MockIsRegistered(*it));
 }
 CHECK(observed.expired()); // host deregistration has removed callable
 CHECK(MockCount()==0);
 CHECK(MockStreamDestructors()==2);
 CHECK(NativeComplete::destroyed==2);
 CHECK(!MockUnregister(k0));
 std::printf("PASS cross-EXE/DLL MSVC std::function NativeCreator ABI mock; "
  "16-byte keys, eager construction, canonical, duplicate, callable retention, "
  "explicit reverse unregistration; created=%d destroyed=%d\n",
  NativeComplete::created,NativeComplete::destroyed);
 return 0;
}
