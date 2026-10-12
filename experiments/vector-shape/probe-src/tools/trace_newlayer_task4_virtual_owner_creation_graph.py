"""Native static graph from known New Shape BEE_NewLayerTask<4> virtual entry,
including direct calls/jmps. Independent both pinned binaries. No live AE.
"""
from pathlib import Path
from collections import deque
import pefile,bisect,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x54e920,0x3a7ca0),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x56d660,0x3b4110)}
out={}
for ver,(path,first,target) in cfg.items():
 p=pefile.PE(path);data=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 sections=[(s.VirtualAddress,s.VirtualAddress+s.Misc_VirtualSize) for s in p.sections if s.Characteristics&0x20000000]
 pd=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pd]
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 by_start={};cache={}
 def bounds(rv):
  k=bisect.bisect_right(starts,rv)-1
  return pd[k] if k>=0 and rv<pd[k][1] else (rv,rv+128)
 def xrefs(rv):
  if rv in cache:return cache[rv]
  a,b=bounds(rv);found=[]
  for x in cs.disasm(data[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
   if x.mnemonic not in ("call","jmp") or not x.operands or x.operands[0].type!=X86_OP_IMM:continue
   dst=x.operands[0].imm-base
   if any(a<=dst<b for a,b in sections):
    found.append((dst,x.address-base))
  cache[rv]=found
  return found
 q=deque([(first,[first],[])]);seen={first};path=None
 while q and len(seen)<5000:
  rv,visited,sites=q.popleft()
  if rv==target:
   path={"functions":[hex(x) for x in visited],"callsites":[hex(x) for x in sites]}
   break
  if len(visited)>=9:continue
  for dst,callsite in xrefs(rv):
   if dst in seen:continue
   seen.add(dst)
   q.append((dst,visited+[dst],sites+[callsite]))
 print(ver,"visited",len(seen),"path",path,flush=True)
 print(ver,"v1 direct",[(hex(dst),hex(site)) for dst,site in xrefs(first)],flush=True)
 out[ver]={"virtual_entry_rva":hex(first),"goal_create_attach_rva":hex(target),
 "depth_limit":8,"explored":len(seen),"direct_path":path,
 "first_edges":[{"dst":hex(a),"callsite":hex(b)} for a,b in xrefs(first)]}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_newlayer_task4_vmethod_owner_creation_graph_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L direct static graph from exact MSVC RTTI vtable slot1 to native owner creator; opaque indirect edges not traversed","versions":out},indent=2)+"\n")
print("SAVED",dst)
