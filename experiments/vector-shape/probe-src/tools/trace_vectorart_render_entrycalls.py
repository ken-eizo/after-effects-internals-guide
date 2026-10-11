from pathlib import Path
import pefile,subprocess,re,json,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
R=Path(r"D:\Developer\After Effects Internals Guide")
rx=re.compile(r"^\s*(\d+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]{8})\s+(\S+)")
terms=["?GetVectorArt@BEE_VectorLayer@@","?PopulateVectorArt@BEE_VectorStream@@","?Rasterize2DGraph@BEE_VectorLayer@@","??0Path@BEE_VectorArt@@","??0StreamBasedFilter@BEE_VectorArt@@"]
result={}
for year,path in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")]:
    p=pefile.PE(path);data=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
    names={}
    for line in subprocess.run(["dumpbin","/exports",path],capture_output=True,text=True,errors="replace").stdout.splitlines():
        m=rx.match(line)
        if m:names[int(m.group(3),16)]=m.group(4)
    bounds=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
    starts=[a for a,b in bounds]
    iat={i.address:(lib.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")) for lib in p.DIRECTORY_ENTRY_IMPORT for i in lib.imports if i.name}
    cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
    out=[]
    for addr,name in names.items():
        if not any(t in name for t in terms):continue
        j=bisect.bisect_right(starts,addr)-1
        if j<0 or addr>=bounds[j][1]:continue
        stop=bounds[j][1];end=min(stop,addr+9000)
        instr=[]
        for x in cs.disasm(data[p.get_offset_from_rva(addr):p.get_offset_from_rva(addr)+(end-addr)],base+addr):
            if x.mnemonic not in ("call","jmp"):continue
            target=None
            if x.operands and x.operands[0].type==X86_OP_MEM and x.operands[0].mem.base==X86_REG_RIP:target=x.address+x.size+x.operands[0].mem.disp
            elif x.op_str.startswith("0x"):
                try:target=int(x.op_str,16)
                except ValueError:pass
            instr.append({"at":hex(x.address-base),"import":iat.get(target,""),
                          "export":names.get(target-base,"") if target else "","target":hex(target-base) if target else ""})
        out.append({"name":name,"rva":hex(addr),"method_end":hex(stop),"calls":instr})
    result[year]=out
    print(year,[(x["name"][:48],len(x["calls"])) for x in out],flush=True)
dest=R/"datasets"/"ae-vectorart-render-entry-calls-2025-2026.json"
dest.write_text(json.dumps({"evidence":"E2-L static direct/IAT calls; bounded x64 runtime function table","versions":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest)
