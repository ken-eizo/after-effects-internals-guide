// EXP-SHAPE-022: procedural native cubic Beziers -> actual SVG paths.
// Loads the real VectorBridgeAEGP.aex via minimal standalone PICA host.
// Demonstrates usable code-generated vector artwork WITHOUT pixel rasterization.
// This converter does NOT call BEE, produce native Contents itself, or run in AE.
#include <windows.h>
#include <cstdint>
#include <cstdlib>
#include <cmath>
#include <cstring>
#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <iomanip>
#include <vector>
#include <limits>
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "SPBasic.h"
#include "SPSuites.h"
#include "VectorBridgeSuite.h"

namespace {
SPSuitesSuite api{};
SPBasicSuite basic{};
const CNL_VectorBridgeSuite1* bridge = nullptr;
constexpr double pi=3.1415926535897932384626433832795;
constexpr double canvas=1024.0;
void Require(bool yes,const char* msg) {
 if(!yes){ std::cerr << "FAIL: " << msg << "\n"; std::exit(2); }
}
SPErr Add(SPSuiteListRef,SPPluginRef,const char* name,int32 version,int32,
 const void* vtable,SPSuiteRef* out) {
 if(!name || std::strcmp(name,kCNLVectorBridgeSuite1) ||
    version!=kCNLVectorBridgeSuiteVersion1 || !out || !vtable)return 41;
 bridge=static_cast<const CNL_VectorBridgeSuite1*>(vtable);
 *out=reinterpret_cast<SPSuiteRef>(0x1234);
 return 0;
}
SPErr Acquire(const char* name,int32 version,const void** out) {
 if(!out || !name)return 42;
 *out=nullptr;
 if(!std::strcmp(name,kSPSuitesSuite) && version==kSPSuitesSuiteVersion) {
    *out=&api;return 0;
 }
 if(!std::strcmp(name,kCNLVectorBridgeSuite1) &&
    version==kCNLVectorBridgeSuiteVersion1 && bridge) {
    *out=bridge;return 0;
 }
 return 43;
}
SPErr Release(const char*,int32){return 0;}
struct Pt{double x,y;};
Pt Transform(double x,double y,double theta,double ox,double oy,double scale){
 const double c=std::cos(theta),s=std::sin(theta);
 return {ox+scale*(x*c-y*s),oy+scale*(x*s+y*c)};
}
void Print(std::ostream& o,Pt pt) {
 Require(std::isfinite(pt.x)&&std::isfinite(pt.y),"nonfinite vector coordinate");
 o<<pt.x<<","<<pt.y;
}
std::string Path(const CNL_VectorCubicV1* curves,uint32_t count,
 double theta,double cx,double cy,double factor){
 std::ostringstream o;
 o<<std::fixed<<std::setprecision(5);
 for(uint32_t j=0;j<count;++j) {
  const auto& b=curves[j];
  if(j==0) {o<<"M ";Print(o,Transform(b.x0,b.y0,theta,cx,cy,factor));o<<" "; }
  o<<"C ";Print(o,Transform(b.x1,b.y1,theta,cx,cy,factor));o<<" ";
  Print(o,Transform(b.x2,b.y2,theta,cx,cy,factor));o<<" ";
  Print(o,Transform(b.x3,b.y3,theta,cx,cy,factor));o<<" ";
 }
 o<<"Z";
 return o.str();
}
}
int main(int argc,char* argv[]){
 if(argc!=7){
  std::cerr<<"usage: VectorBridgeToSVG.exe provider.aex output.svg time_num time_den "
   "path_kind repeat_count\nExample: provider.aex output.svg 12 24 1 24\n";
  return 1;
 }
 const long long time_num=_strtoi64(argv[3],nullptr,10);
 const long long time_den=_strtoi64(argv[4],nullptr,10);
 const long long kind=_strtoi64(argv[5],nullptr,10);
 const long long repeats=_strtoi64(argv[6],nullptr,10);
 Require(time_den>0 && kind>=0 && kind<=1,"bad kind or timeline denominator");
 Require(repeats>=1 && repeats<=256,"repeats out of [1, 256]");
 const HMODULE module=LoadLibraryA(argv[1]);
 Require(module!=nullptr,"cannot load VectorBridgeAEGP AEX");
 using Init=A_Err (*)(SPBasicSuite*,A_long,A_long,AEGP_PluginID,AEGP_GlobalRefcon*);
 const auto init=reinterpret_cast<Init>(GetProcAddress(module,"EntryPointFunc"));
 Require(init!=nullptr,"missing AEGP entrypoint");
 api.AddSuite=Add;
 basic.AcquireSuite=Acquire;basic.ReleaseSuite=Release;
 Require(init(&basic,26,5,0,nullptr)==A_Err_NONE && bridge,
         "provider did not register procedural PICA vector service");
 CNL_VectorPathInfoV1 desc{sizeof(CNL_VectorPathInfoV1),0,0,0};
 Require(bridge->DescribePath(static_cast<uint32_t>(kind),&desc)==A_Err_NONE,
         "DescribePath failed");
 Require(desc.closed && desc.cubic_count>=1 && desc.cubic_count<10000,
         "unexpected procedural geometry dimensions");
 std::vector<CNL_VectorCubicV1> curves(desc.cubic_count);
 uint32_t actual=0;
 Require(bridge->CopyCubicPath(static_cast<uint32_t>(kind),time_num,time_den,
  curves.data(),static_cast<uint32_t>(curves.size()),&actual)==A_Err_NONE &&
  actual==curves.size(),"CopyCubicPath failed");
 std::ofstream output(argv[2],std::ios::binary|std::ios::trunc);
 Require(bool(output),"cannot create SVG output");
 output<<"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
 output<<"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1024\" "
  "height=\"1024\" viewBox=\"0 0 1024 1024\">\n";
 output<<"<title>CompNodeAE procedural vector geometry test</title>\n";
 output<<"<desc>Original cubic path data from a separately compiled AEGP via a PICA "
   "Suite; per-instance affine transforms computed here; no raster pixels.</desc>\n";
 const int n=int(repeats);
 for(int i=0;i<n;++i){
  const double angle=(2*pi*i)/n;
  const double theta=angle+0.2*time_num/double(time_den);
  const double radial=(n==1)?0:265;
  const double x=canvas/2+radial*std::cos(angle);
  const double y=canvas/2+radial*std::sin(angle);
  const double factor=(n==1)?2.2:0.95;
  const int red=45+(i*41)%185;
  const int green=70+(i*59)%156;
  const int blue=115+(i*73)%120;
  output<<"<path id=\"cnl-path-"<<i<<"\" d=\""<<Path(curves.data(),actual,theta,x,y,factor)
   <<"\" fill=\"none\" stroke=\"rgb("<<red<<","<<green<<","<<blue
   <<")\" stroke-width=\""<<std::fixed<<std::setprecision(2)
   <<(n==1?12.:3.5)<<"\" stroke-linecap=\"round\"/>\n";
 }
 output<<"</svg>\n";
 output.flush();
 Require(bool(output),"SVG write failed");
 std::cout<<"PASS native_pica_aex=1 provider_cubics="<<actual
          <<" rendered_paths="<<n<<" time="<<time_num<<"/"<<time_den
          <<" no_raster=1 destination="<<argv[2]<<"\n";
 return 0;
}
