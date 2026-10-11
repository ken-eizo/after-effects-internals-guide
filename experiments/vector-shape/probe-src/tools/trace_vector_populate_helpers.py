"""Inspect unexported recursive helper immediately downstream of PopulateVectorArt.
Bound by x64 .pdata, resolve external import/direct exports, no execution.
"""
from pathlib import Path
from bisect import bisect_right
import pefile, subprocess, re, json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6ecc70),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x710f90)}
RX=re.compile(r"^\s*(\d+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]{8})\s+(\S+)")
results={}
for year,(path,at) in cfg.items():
    p=pefile.PE(path);raw=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
    exp={}
    for l in subprocess.run(["dumpbin","/exports",path],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
        m=RX.match(l)
        if m:exp[int(m.group(3),16)]=m.group(4)
    iat={i.address:m.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for m in p.DIRECTORY_ENTRY_IMPORT for i in m.imports if i.name}
    boundaries=sorted((f.struct.BeginAddress,f.struct.EndAddress) for f in p.DIRECTORY_ENTRY_EXCEPTION)
    starts=[x[0] for x in boundaries]
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
    sections=[]
    todo=[(at,0)]
    seen=set()
    while todo and len(sections)<12:
        rva,depth=todo.pop(0)
        if depth>3:continue
        idx=bisect_right(starts,rva)-1
        if idx<0 or rva>=boundaries[idx][1]:continue
        a,b=boundaries[idx]
        if a in seen:continue
        seen.add(a)
        if b-a>18000:continue
        calls=[];refs=[]
        for ins in md.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)],base+a):
            dest=None
            if ins.operands and ins.mnemonic in ("call","jmp","lea"):
                op=ins.operands[-1] if ins.mnemonic=="lea" else ins.operands[0]
                if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:dest=ins.address+ins.size+op.mem.disp
                elif op.type==X86_OP_IMM:dest=op.imm
            if dest is None:continue
            dest_rva=dest-base
            if ins.mnemonic in ("call","jmp"):
                calls.append({"site":hex(ins.address-base),"operation":ins.mnemonic,"target_rva":hex(dest_rva),"imported":iat.get(dest,""),"exported":exp.get(dest_rva,"")})
                if 0<dest_rva<len(raw) and not iat.get(dest) and not exp.get(dest_rva) and depth<3:
                    if abs(dest_rva-at)<0x22000:todo.append((dest_rva,depth+1))
            elif ins.mnemonic=="lea":
                refs.append({"site":hex(ins.address-base),"target_rva":hex(dest_rva),"exported":exp.get(dest_rva,"")})
        sections.append({"start":hex(a),"end":hex(b),"depth":depth,"calls":calls,"lea_refs":refs})
    results[year]=sections
    print("YEAR",year,"sections",len(sections),flush=True)
    for s in sections:
        print(s["start"],s["end"],"depth",s["depth"],"calls",len(s["calls"]),flush=True)
        for c in s["calls"][:90]:
            print(" ",c["site"],c["imported"][:115] or c["exported"][:115] or c["target_rva"],flush=True)
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-native-vector-populate-recursive-helpers-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L PE exception/function-boundary static call graph; no dynamic execution","versions":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest)
