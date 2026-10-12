// CompNodeAE Vector Renderer prototype. Original authoring geometry stays cubic.
// Only the final stage flattens the cubic stroke to coverage pixels for PF_World.
// No Adobe private API; no global mutable state; direct background-blend on 8bpc.
#pragma once
#include "VectorBridgeSuite.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cstddef>
#include <vector>

namespace cnlvec {
constexpr double PI = 3.1415926535897932384626433832795;
struct Point { double x=0, y=0; };
struct Color { uint8_t r=76, g=228, b=255; };
struct Config {
    int copies=14;
    double orbit=210.0;
    double scale=0.66;
    double stroke=4.5;
    double rotation=0.0;  // angle (radians) at the requested AE render time
    bool clearInput=false;
    Color color;
};
struct Pixel8 { uint8_t alpha, red, green, blue; };
static_assert(sizeof(Pixel8)==4,"Required alpha-red-green-blue PF_Pixel8 layout");
inline Point Bezier(const CNL_VectorCubicV1& c, double t) {
    const double u=1.0-t, uu=u*u, tt=t*t;
    const double a=uu*u, b=3.0*uu*t, d=3.0*u*tt, e=tt*t;
    return { a*c.x0+b*c.x1+d*c.x2+e*c.x3,
             a*c.y0+b*c.y1+d*c.y2+e*c.y3 };
}
inline Point Transform(Point p,double angle,double scale, double cx,double cy){
    const double co=std::cos(angle), si=std::sin(angle);
    return {cx+scale*(p.x*co-p.y*si),cy+scale*(p.x*si+p.y*co)};
}
inline unsigned char Channel(double v){
    return static_cast<unsigned char>(std::lround(std::clamp(v,0.0,255.0)));
}
inline double Coverage(double px,double py,double x1,double y1,double x2,double y2,double stroke) {
    const double dx=x2-x1,dy=y2-y1,den=dx*dx+dy*dy;
    const double t=den>1e-12?std::clamp(((px-x1)*dx+(py-y1)*dy)/den,0.0,1.0):0.0;
    const double ex=px-(x1+t*dx),ey=py-(y1+t*dy);
    const double dist=std::sqrt(ex*ex+ey*ey);
    // 1-pixel analytic edge AA; distance from the vector centerline.
    return std::clamp(stroke*0.5+0.5-dist,0.0,1.0);
}
inline void Clear(Pixel8* out, ptrdiff_t bytes_per_row, int height, int width) {
    for(int y=0;y<height;++y)
        std::memset(reinterpret_cast<uint8_t*>(out)+y*bytes_per_row,0,
                    static_cast<size_t>(width)*sizeof(Pixel8));
}
inline void Segment(Pixel8* output, ptrdiff_t rowbytes, int width,int height,
                    Point a,Point b,double stroke, Color color){
    const double margin=std::max(1.0,stroke*0.5+1.5);
    const int xmin=std::max(0,int(std::floor(std::min(a.x,b.x)-margin)));
    const int xmax=std::min(width-1,int(std::ceil(std::max(a.x,b.x)+margin)));
    const int ymin=std::max(0,int(std::floor(std::min(a.y,b.y)-margin)));
    const int ymax=std::min(height-1,int(std::ceil(std::max(a.y,b.y)+margin)));
    if(xmax<xmin||ymax<ymin)return;
    for(int y=ymin;y<=ymax;++y){
        auto* row=reinterpret_cast<Pixel8*>(reinterpret_cast<uint8_t*>(output)+y*rowbytes);
        for(int x=xmin;x<=xmax;++x){
            const double alpha=Coverage(double(x)+0.5,double(y)+0.5,
                                        a.x,a.y,b.x,b.y,stroke);
            if(alpha<0.001)continue;
            Pixel8& p=row[x];
            const double rest=1.0-alpha;
            p.red=Channel(color.r*alpha+p.red*rest);
            p.green=Channel(color.g*alpha+p.green*rest);
            p.blue=Channel(color.b*alpha+p.blue*rest);
            p.alpha=Channel(255.0*alpha+p.alpha*rest);
        }
    }
}
inline bool Draw(const CNL_VectorCubicV1* cubics, uint32_t cubic_count,
                 Pixel8* output, ptrdiff_t rowbytes, int width,int height,
                 const Config& config) {
    if(!output||!cubics||!cubic_count||cubic_count>4096||
       width<=0||height<=0||rowbytes<ptrdiff_t(width*4)||
       config.copies<1||config.copies>128) return false;
    if(config.clearInput) Clear(output,rowbytes,height,width);
    const double rotation=std::remainder(config.rotation,2.0*PI);
    const double centerx=width/2.0, centery=height/2.0;
    const double effective_scale=std::clamp(config.scale,0.01,8.0);
    const double stroke=std::clamp(config.stroke,0.2,90.0);
    const double orbit=std::clamp(config.orbit,0.0,double(std::max(width,height))*2.0);
    // All time-dependent geometry is evaluated as cubic Bezier data BEFORE this
    // output raster conversion. CNL_VectorCubicV1 is the extension's vector type.
    for(int instance=0;instance<config.copies;++instance){
        const double angle=2.0*PI*double(instance)/config.copies;
        const double theta=angle+rotation;
        const double ox=centerx+orbit*std::cos(angle);
        const double oy=centery+orbit*std::sin(angle);
        Color shade=config.color;
        // Small brightness variation makes interlocking geometry readable.
        const double varying=0.72+0.28*std::sin(2.0*angle+rotation);
        shade.r=Channel(25.0+double(config.color.r)*varying);
        shade.g=Channel(25.0+double(config.color.g)*varying);
        shade.b=Channel(25.0+double(config.color.b)*varying);
        constexpr int STEPS=18; // max cubic subdivision chord error ~0.1 px default
        for(uint32_t s=0;s<cubic_count;++s){
            Point prev=Transform(Bezier(cubics[s],0.0),theta,effective_scale,ox,oy);
            for(int j=1;j<=STEPS;++j){
                Point next=Transform(Bezier(cubics[s],double(j)/STEPS),
                                     theta,effective_scale,ox,oy);
                Segment(output,rowbytes,width,height,prev,next,stroke,shade);
                prev=next;
            }
        }
    }
    return true;
}
inline void BuiltinEllipse(CNL_VectorCubicV1 (&out)[4],double t,uint32_t kind) {
    constexpr double k=0.5522847498307936;
    const double rad=100.0+25.0*std::sin(t*1.3);
    const double rx=rad,ry=rad*(kind==0?1.0:0.45);
    const double xx[5]={rx,0,-rx,0,rx}, yy[5]={0,ry,0,-ry,0};
    const double dx[4]={0,-rx,0,rx},dy[4]={ry,0,-ry,0};
    for(unsigned i=0;i<4;++i){
        auto& c=out[i];c.x0=xx[i];c.y0=yy[i];c.x3=xx[i+1];c.y3=yy[i+1];
        c.x1=xx[i]+dx[i]*k;c.y1=yy[i]+dy[i]*k;
        c.x2=xx[i+1]-dx[(i+1)%4]*k;c.y2=yy[i+1]-dy[(i+1)%4]*k;
    }
}
} // namespace cnlvec
