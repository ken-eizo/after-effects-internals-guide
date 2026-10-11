"""Find direct native callers of FLT_FCSeqSpec::AddStreamToUILayout.
Indirect virtual invocations are not captured.
"""
import pefile,hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll"}
out={}
for year,fn in files.items():
 data=Path(fn).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 syms={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 targets=[(s,r) for s,r in syms.items() if s.startswith("?AddStreamToUILayout@FLT_FCSeqSpec@@")]
 assert len(targets)==1
 name,target=targets[0]
 calls=[]
 cs=Cs(CS_ARCH_X86,CS_MODE_64)
 for sec in p.sections:
  if not sec.Characteristics&0x20000000:continue
  cs.skipdata=True
  for addr,size,mn,op in cs.disasm_lite(sec.get_data(),base+sec.VirtualAddress):
   if mn!="call" or not op.startswith("0x"):continue
   try:t=int(op,16)-base
   except ValueError:continue
   if t==target:calls.append(hex(addr-base))
 out[year]={"flt_sha256":hashlib.sha256(data).hexdigest(),"symbol":name,
            "target_rva":hex(target),"direct_call_sites":calls,
            "indirect_calls_excluded":True}
 print(year,"AddStreamToUILayout direct callsites",calls,flush=True)
dest=Path(r"D:\Developer\ShapeLayerAE\results\flt_fcseqspec_addlayout_direct_calls_2025_2026.json")
dest.write_text(json.dumps({"classification":"E2-L direct CALL scan only","versions":out},indent=2)+"\n")
print("SAVED",dest)
