"""EXP-SHAPE-023 callsites to generic native indexed child command, vector command,
and SVG importer. Do all operations enter same owner-independent tree API?
Scans installed BEE.dll 2025/26 .text direct relative CALL/JMP only.
"""
from pathlib import Path
import pefile,subprocess,re,bisect,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
root=Path(r"D:\Developer\After Effects Internals Guide")
versions={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
queries=("BEE_CmdAddToIndexedStreamGroup@@","BEE_CmdAddVectorProperty@@",
"BEE_CmdPasteSVGIntoLayer@@","BEE_PasteSVGIntoComp@@",
"BEE_CmdNewVectorLayer@@","BEE_GetShapePathsVec@@",
"BEE_IsShapeGroupOwnerStreamPath@@","BEE_IsShapeGroupStreamPath@@",
"BEE_IsShapeStreamPath@@","BEE_CmdRemoveIndexedGroupEntry@@")
rx=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
report={}
for year,exe in versions.items():
 raw=exe.read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 syms={}
 for line in subprocess.run(["dumpbin","/exports",str(exe)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  match=rx.match(line)
  if match:syms[int(match.group(1),16)]=match.group(2)
 targets={addr:name for addr,name in syms.items() if any(q in name for q in queries)}
 callsites={key:[] for key in targets}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in pdata]
 decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.skipdata=True
 inspected=0
 for sec in p.sections:
  if not sec.Characteristics & 0x20000000:continue
  for loc,size,opc,txt in decoder.disasm_lite(sec.get_data(),base+sec.VirtualAddress):
   inspected+=1
   if opc!="call" and opc!="jmp":continue
   if not txt.startswith("0x"):continue
   try:target=int(txt,16)-base
   except ValueError:continue
   if target not in targets:continue
   caller=loc-base
   i=bisect.bisect_right(starts,caller)-1
   owner=starts[i] if i>=0 and caller<pdata[i][1] else None
   callsites[target].append({"callsite":hex(caller),"caller_function_start":hex(owner) if owner is not None else None,
                             "caller_export":syms.get(owner,"") if owner is not None else "", "type":opc})
 data=[]
 for addr,name in sorted(targets.items()):
  calls=callsites[addr]
  item={"symbol":name,"rva":hex(addr),"num_direct_calls":len(calls),"callsites":calls}
  data.append(item)
  print(year,name.split("@")[0],hex(addr),"direct_calls",len(calls),flush=True)
  for call in calls[:20]:print(" ",call["callsite"],call["caller_function_start"],call["caller_export"][:130],flush=True)
 report[year]={"hash_sha256":hashlib.sha256(raw).hexdigest(),"instruction_count":inspected,"results":data}
dest=root/"datasets/ae-native-indexed-contents-owner-command-xrefs-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L direct call and export-boundary evidence; no runtime execution, indirect calls not scanned",
"years":report},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
