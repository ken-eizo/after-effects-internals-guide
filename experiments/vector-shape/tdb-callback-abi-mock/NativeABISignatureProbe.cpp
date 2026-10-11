// EXP-SHAPE-031: compare MSVC std::function callback mangling against
// Adobe's ACTUAL exported TDB StreamFactory::RegisterFactoryFunc signature.
//
// This compilation unit NEVER includes Adobe SDK/private headers, links
// against Adobe DLLs, or calls any Adobe code.
#include <functional>
class TDB_StreamBase;
class TDB_StreamFactory;
class TDB_MatchName;
using AdobeCreatorSignature=TDB_StreamBase*(
 const TDB_MatchName&,TDB_StreamFactory*,bool,unsigned int,bool);
using AdobeCreatorErasure=std::function<AdobeCreatorSignature>;

// External linkage forces a C++ decorated symbol in the OBJ, including
// TDB class types, callback args, bool,unsigned int,bool return pointer,
// and the exact std::function template argument.
bool CNL_ABI_SignatureComparator(const TDB_MatchName&,AdobeCreatorErasure,bool){
 return true;
}
