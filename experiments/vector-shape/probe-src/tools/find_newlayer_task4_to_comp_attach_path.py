"""Find actual native CompItem attachment reachability from the new-layer
task factory worker, across <=7 direct x64 internal calls/jumps (both versions).
No runtime host invocation.
"""
from pathlib import Path
from collections import deque
import pefile,bisect,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x3151d0,0x392120),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x31e800,0x39d4d0)}
out={}
for y,(file,entry,goal) in cfg.items():
 p=pefile.PE(file);blob=Path(file).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 pd=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 beginnings=[x[0] for x in pd]
 exec_sections=[(s.VirtualAddress,s.VirtualAddress+s.Misc_VirtualSize) for s in p.sections if s.Characteristics&0x20000000]
 dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True;cache={}
 def edges(rv):
  if rv in cache:return cache[rv]
  ix=bisect.bisect_right(beginnings,rv)-1
  a,b=pd[ix] if ix>=0 and rv<pd[ix][1] else (rv,rv+100)
  xs=[]
  for x in dec.disasm(blob[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
   if x.mnemonic not in ("call","jmp") or not x.operands or x.operands[0].type!=X86_OP_IMM:continue
   dest=x.operands[0].imm-base
   if any(lo<=dest<hi for lo,hi in exec_sections):
    xs.append((dest,x.address-base))
  cache[rv]=xs
  return xs
 queue=deque([(entry,[entry],[])]);seen={entry};answer=None
 while queue and len(seen)<6500:
  node,path,sites=queue.popleft()
  if node==goal:
   answer={"node_path":[hex(x) for x in path],"call_sites":[hex(x) for x in sites]};break
  if len(path)>8:continue
  for target,site in edges(node):
   if target in seen:continue
   seen.add(target);queue.append((target,path+[target],sites+[site]))
 print(y,"worker->CompAttach direct route?",bool(answer),"inspected",len(seen),"route",answer,flush=True)
 out[y]={"new_task4_factory_worker":hex(entry),"CompItem_AttachLayerToCompOnly":hex(goal),
         "discovered_direct_path":answer,"visited_functions":len(seen)}
target=Path(r"D:\Developer\ShapeLayerAE\results\bee_newtask4_creation_to_comp_attach_reachability_2025_2026.json")
target.write_text(json.dumps({"evidence":"E2-L actual x64 code static bounded traversal, not runtime branch witness","versions":out},indent=2)+"\n")
print("SAVED",target)
