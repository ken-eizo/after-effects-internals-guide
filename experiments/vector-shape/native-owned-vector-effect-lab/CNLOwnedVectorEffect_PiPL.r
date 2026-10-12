#include "AEConfig.h"
#include "AE_EffectVers.h"
#ifndef AE_OS_WIN
#include "AE_General.r"
#endif
resource 'PiPL' (16000) {
 {
  Kind { AEEffect },
  Name { "CNL Owned Vector Document (Research)" },
  Category { "CNL Research" },
#ifdef AE_OS_WIN
#if defined(AE_PROC_INTELx64)
  CodeWin64X86 { "EffectMain" },
#elif defined(AE_PROC_ARM64)
  CodeWinARM64 { "EffectMain" },
#endif
#else
  CodeMacIntel64 { "EffectMain" },
#endif
  AE_PiPL_Version { 2, 0 },
  AE_Effect_Spec_Version { PF_PLUG_IN_VERSION, PF_PLUG_IN_SUBVERS },
  AE_Effect_Version { 524290 },
  AE_Effect_Info_Flags { 0 },
  // PF_OutFlag_NON_PARAM_VARY: time-dependent geometry, even on a still.
  AE_Effect_Global_OutFlags { 0x4 },
  // PF_OutFlag2_SUPPORTS_THREADED_RENDERING; no per-render global mutation.
  AE_Effect_Global_OutFlags_2 { 0x8000000 },
  AE_Effect_Match_Name { "CNL Owned Vector Document" },
  AE_Reserved_Info { 0 },
  AE_Effect_Support_URL {
     "https://github.com/ken-eizo/after-effects-internals-guide"
  }
 }
};
