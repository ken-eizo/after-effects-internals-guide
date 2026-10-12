"""Verify arguments at BEE_NewLayerTask<4>::Execute call to
BEE_Layer::CreateLayerFromType in exact native code.
No host process involvement.
"""
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
import pefile,bisect,json
rows={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x3151d0,0x3152b2),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x31e800,0x31e8f0)}
out={}
for y,(path,origin,call) in rows.items():
 blob=Path(path).read_bytes();p=pefile.PE(data=blob);base=p.OPTIONAL_HEADER.ImageBase
 pd=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 a,b=next((lo,hi) for lo,hi in pd if lo<=origin<hi)
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 ins=list(cs.disasm(blob[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a))
 candidates=[i for i,x in enumerate(ins) if x.address-base==call]
 assert len(candidates)==1
 k=candidates[0]
 cut=[{"at":hex(x.address-base),"asm":x.mnemonic+" "+x.op_str} for x in ins[k-24:k+17]]
 print("VERSION",y,"around factory call:")
 for row in cut: print(row["at"],row["asm"],flush=True)
 out[y]={"callsite":hex(call),"instructions_around":cut}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_newlayer_task4_native_factory_call_arguments_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L actual native BEE_NewLayerTask<4> worker factory parameters from pinned PE code","versions":out},indent=2)+"\n")
print("SAVED",dst)
