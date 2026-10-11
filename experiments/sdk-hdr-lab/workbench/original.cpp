
#include <iostream>
#include <iomanip>
#include <string>
#include <cstdlib>
#include <cmath>
#include <limits>
#include "SmartyPants.h"
static_assert(sizeof(A_u_short)==2 && sizeof(A_long)==4 && sizeof(PF_FpShort)==4, "SDK ABI widths");
static 
A_long 
Pin32(
	A_long bottom, 
	A_long target, 
	A_long top)
{
	return MAX(bottom, MIN(target, top));
}

static A_long
RoundDouble(
	PF_FpLong	xF)
{
	A_long	retF = 0;
	
	if (xF > 0) {
		retF = (A_long)((xF + 0.5));
	} else {
		if ((A_long)(xF + 0.5) == (xF + 0.5)) {
			retF = (A_long)xF;
		} else {
			retF = (A_long)(xF - 0.5);
		}
	}
	return retF;
}

static void
FindDeepHSL(	
	A_u_short 	cmax,
	A_u_short 	cmidSu,
	A_u_short 	cminSu,
	A_long 		*hueP,
	A_long 		*satP,
	A_long 		*lightP)
{
	*lightP 	= (A_long)cminSu + cmax;
	*satP 		= (A_long)cmax - cminSu;
	
	if (*satP != 0){
		*hueP = (4096 * ((A_long)cmidSu - cminSu) + ((*satP) >> 1)) / (*satP);
	} else{
		*hueP = 0;
	}
}

static void 
RGBtoHSL16(	
	A_u_short 	r,
	A_u_short 	g,
	A_u_short 	b,
	A_long 		*H,
	A_long 		*S,
	A_long 		*L )
{
	if (g >= b) {
		if (r >= b) {
			if (r >= g) {
				FindDeepHSL (r, g, b, H, S, L);
			} else {
				FindDeepHSL (g, r, b, H, S, L);
				*H = 8192 - *H;
			}
		} else {
			FindDeepHSL (g, b, r, H, S, L);
			*H = 8192 + *H;
		}
	} else {
		if (r >= g)	{
			if (r >= b)	{
				FindDeepHSL (r, b, g, H, S, L);
				if (*H != 0){
					*H = 24576 - *H;
				}
			} else {
				FindDeepHSL (b, r, g, H, S, L);
				*H = 16384 + *H;
			}
		} else {
			FindDeepHSL (b, g, r, H, S, L);
			*H = 16384 - *H;
		}
	}
}

static void 
PutHSLFloat (
	A_long 		hue,
	A_long 		sat,
	A_long 		light,
	PF_FpShort 	*cmax,
	PF_FpShort 	*cmid,
	PF_FpShort 	*cmin)

{
	*cmin = (PF_FpShort) (light / 32768.0);
	*cmid = (PF_FpShort) ((light + (( (hue * sat) + 2048) / 4096)) / 32768.0);
	*cmax = (PF_FpShort) ((sat + light) / 32768.0);
}

static void 
HSLtoRGBFloat(	
	A_long 		H,							   
	A_long 		S,
	A_long 		L,
	PF_FpShort 	*r,
	PF_FpShort 	*g,
	PF_FpShort 	*b )

{
	A_long temp = L;

	/* Find maximum gap */
	if (temp > 32768){
		temp = 65536 - temp;
	}
	/* Clamp gap to maximum */
	if (S > temp){
		S = temp;
	}
	/* Convert lightness to minimum */
	L = (L - S) >> 1;
	
	if (H < 4096){
		PutHSLFloat (H, S, L, r, g, b);
	} else if (H < 8192) {
		PutHSLFloat (8192 - H, S, L, g, r, b);
	} else if (H < 12288) {
		PutHSLFloat (H - 8192, S, L, g, b, r);
	} else if (H < 16384) {
		PutHSLFloat (16384 - H, S, L, b, g, r);
	} else if (H < 20480) {
		PutHSLFloat (H - 16384, S, L, b, r, g);
	} else {
		PutHSLFloat (24576 - H, S, L, r, b, g);
	}
}

static void
RGBtoYIQ(	
	A_u_short		rSu,
	A_u_short		gSu,
	A_u_short		bSu,
	A_FpLong		*yP,
	A_FpLong		*iP,
	A_FpLong		*qP ) 

{
	*yP = rSu * 0.2989 + gSu * 0.5866 + bSu * 0.1144;
 	*iP = rSu * 0.5959 - gSu * 0.2741 - bSu * 0.3218;
	*qP = rSu * 0.2113 - gSu * 0.5227 + bSu * 0.3113;
}

static void
YIQtoRGBFloat(	
	A_FpLong		yF,
	A_FpLong		iF,
	A_FpLong      	qF,
	PF_FpShort		*rP,
	PF_FpShort		*gP,
	PF_FpShort		*bP)
{
  	*rP = (PF_FpShort)RoundDouble(yF + iF * 0.9562 + qF * 0.6210) / 32768.0;
	*gP = (PF_FpShort)RoundDouble(yF - iF * 0.2717 - qF * 0.6485) / 32768.0;
	*bP = (PF_FpShort)RoundDouble(yF - iF * 1.1053 + qF * 1.7020) / 32768.0;
}

static PF_Err
InvertPixelFloat(
	void			*refcon, 
	A_long 			x, 
	A_long 			y, 
	PF_PixelFloat 	*in, 
	PF_PixelFloat 	*out)
{
	SmartyPantsDataPlus	*idp 	= reinterpret_cast<SmartyPantsDataPlus*>(refcon);
	SmartyPantsData		*id		= idp->id;

	for (A_long iL = x; iL < idp->outputP->width+x; iL++) {
		A_long	        		hueL, satL, lightL;
		A_FpLong					yF, iF, qF;
 
 		switch (id->channel) {
			case Channel_ALPHA:
				*out = *in;
 				out->alpha = 1.0 - in->alpha;
				break;
			case Channel_RGB:
				out->red 	= 1.0 - in->red;
				out->green 	= 1.0 - in->green;
				out->blue 	= 1.0 - in->blue;
				out->alpha 	= in->alpha;
				break;
			case Channel_RED:
				*out 		= *in;
				out->red 	= 1.0 - in->red;
				break;
			case Channel_GREEN:
				*out 		= *in;
				out->green 	= 1.0 - in->green;
				break;
			case Channel_BLUE:
				*out 		= *in;
				out->blue 	= 1.0 - in->blue;
				break;

				
			case Channel_HLS:
			case Channel_HUE:
			case Channel_LIGHTNESS:
			case Channel_SATURATION:
 
				out->alpha = in->alpha;
 				RGBtoHSL16((A_u_short)(32768.0 * in->red), (A_u_short)(32768.0 * in->green), (A_u_short)(32768.0 * in->blue), &hueL, &satL, &lightL);

				switch (id->channel) {
				case Channel_HLS:
 					hueL =	12288 - hueL;
					if(hueL < 0) {
						hueL = hueL + 24576; 
					}
					satL = PF_MAX_CHAN16 - satL;
					lightL = (PF_MAX_CHAN16 << 1) - lightL;
					break;
				case Channel_HUE:
 					hueL =	12288 - hueL;
					if(hueL < 0) {
						hueL = hueL + 24576; 
					}
 					break;
				case Channel_LIGHTNESS:
					lightL = (PF_MAX_CHAN16 << 1) - lightL;
 					break;
				case Channel_SATURATION:
					satL = PF_MAX_CHAN16 - satL;
 					break;
				}

 				HSLtoRGBFloat(	hueL, 
 								satL, 
 								lightL, 
 								&(out->red), 
 								&(out->green), 
 								&(out->blue));
 
				break;

			case Channel_YIQ:
			case Channel_LUMINANCE:
			case Channel_IN_PHASE_CHROMINANCE:
			case Channel_QUADRATURE_CHROMINANCE:
				out->alpha = in->alpha;
				RGBtoYIQ(	(A_u_short)(32768.0 * in->red), 
							(A_u_short)(32768.0 * in->green), 
							(A_u_short)(32768.0 * in->blue), 
							&yF, 
							&iF, 
							&qF ); 

 				switch (id->channel) {
					case Channel_YIQ:

						yF = PF_MAX_CHAN16 - yF;
						iF = -iF;
						qF = -qF;
	  					break;
					case Channel_LUMINANCE:
						yF = PF_MAX_CHAN16 - yF;
	  					break;
					case Channel_IN_PHASE_CHROMINANCE:
	 					iF = -iF;
						break;
					case Channel_QUADRATURE_CHROMINANCE:
						qF = -qF;
	 					break;
				}
				YIQtoRGBFloat(	yF, 
								iF, 
								qF, 
								&(out->red), 
								&(out->green), 
								&(out->blue)); 

 				break;

			default:
				*out = *in;
				break;
		}

		if (id->blend && (id->channel != Channel_ALPHA)) {
			/*
			out->red 	= (out->red 	+ in->red)		/ 2.0;
			out->green 	= (out->green 	+ in->green)	/ 2.0;
			out->blue 	= (out->blue 	+ in->blue)		/ 2.0;
			*/
			out->red 	= out->red 		+ (((in->red - out->red) 		* id->blend) / 256.0);
			out->green 	= out->green 	+ (((in->green - out->green) 	* id->blend) / 256.0);
			out->blue 	= out->blue 	+ (((in->blue - out->blue) 		* id->blend) / 256.0);
		}
		++in;
		++out;
	}
 	return PF_Err_NONE;
}
int main() {
    int channel, blend;
    std::string r,g,b,a;
    std::cout << std::setprecision(9) << std::scientific;
    while (std::cin >> channel >> blend >> r >> g >> b >> a) {
        SmartyPantsData data{};
        data.channel = channel;
        data.blend = static_cast<A_short>(blend);
        PF_LayerDef world{};
        world.width = 1;
        world.height = 1;
        SmartyPantsDataPlus refcon{};
        refcon.id = &data;
        refcon.outputP = &world;
        PF_PixelFloat input{std::strtof(a.c_str(),nullptr), std::strtof(r.c_str(),nullptr),
                            std::strtof(g.c_str(),nullptr), std::strtof(b.c_str(),nullptr)};
        PF_PixelFloat output{-9,-9,-9,-9};
        PF_Err error = InvertPixelFloat(&refcon, 0, 0, &input, &output);
        std::cout << error << " " << output.alpha << " " << output.red << " "
                  << output.green << " " << output.blue << "\n";
    }
}
