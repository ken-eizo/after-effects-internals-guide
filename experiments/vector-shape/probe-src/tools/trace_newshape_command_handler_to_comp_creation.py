"""Cross-version static call-graph BFS from the resolved NewShape command
table's execution handler to the native type4 Create+Attach function.
All native PE disassembly, no runtime invocation or binary mutation.
"""
from pathlib import Path
import bisect,collections,json,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x646c30,0x3a7ca0),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x660c70,0x3b4110)}
results={}
for y,(path,handler,goal) in cfg.items():
 p=pefile.PE(path);blob=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 pd=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION);starts=[a for a,b in pd]
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 cache={}
 def edges(rva):
  if rva in cache:return cache[rva]
  k=bisect.bisect_right(starts,rva)-1
  a,b=pd[k] if k>=0 and rva<pd[k][1] else (rva,rva+140)
  found=[]
  for i in cs.disasm(blob[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
   if i.mnemonic not in ("call","jmp") or not i.operands or i.operands[0].type!=X86_OP_IMM:continue
   dest=i.operands[0].imm-base
   if 0<=dest<p.OPTIONAL_HEADER.SizeOfImage and any(z.VirtualAddress<=dest<z.VirtualAddress+z.Misc_VirtualSize and z.Characteristics&0x20000000 for z in p.sections):
    found.append({"target":dest,"site":i.address-base,"kind":i.mnemonic})
  cache[rva]=found
  return found
 q=collections.deque([(handler,[handler],[])])
 seen={handler};reached=None
 while q and len(seen)<2800:
  f,pathseen,callseen=q.popleft()
  if f==goal:reached={"function_path":[hex(x) for x in pathseen],"call_sites":[hex(x) for x in callseen]};break
  if len(pathseen)>6:continue
  for edge in edges(f):
   target=edge["target"]
   if target in seen:continue
   seen.add(target)
   q.append((target,pathseen+[target],callseen+[edge["site"]]))
 print(y,"visited",len(seen),"reachable target",bool(reached),"shortest",reached,flush=True)
 print(y,"first handler links",[(hex(x["target"]),hex(x["site"])) for x in edges(handler)],flush=True)
 results[y]={"handler_rva":hex(handler),"goal_comp_creation_rva":hex(goal),
 "functions_explored":len(seen),"max_depth":6,
 "direct_call_shortest_path":reached,
 "first_handler_edges":edges(handler)}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_newshape_command_handler_to_comp_creator_callgraph_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L static direct machine-call CFG BFS, not runtime proof of conditional branch execution","versions":results},indent=2)+"\n")
print("SAVED",dst)
