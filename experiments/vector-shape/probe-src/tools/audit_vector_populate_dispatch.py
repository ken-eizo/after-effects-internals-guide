"""Static map of native Shape evaluator and input subtypes. No Adobe code executed."""
from pathlib import Path
from bisect import bisect_right
import pefile,subprocess,re,json,hashlib,collections
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
BINS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
RX=re.compile(r"^\s*(\d+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]{8})\s+(\S+)")
out={}
for ver,path in BINS.items():
    raw=path.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
    exp={}
    for l in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
        m=RX.match(l)
        if m:exp[int(m.group(3),16)]=m.group(4)
    target=[(rva,n) for rva,n in exp.items() if ("PopulateVectorArt@BEE_VectorStream@@" in n or
         ("VectorArt" in n and "@BEE_VectorStream@@" in n) or
         ("VectorArt" in n and "@BEE_VectorLayer@@" in n) or
         ("@BEE_VectorStream@@" in n and any(t in n for t in ("Register","Create","GetShape","Convert","Append","Play","Filter","Populate","Apply"))))]
    funcs=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
    begins=[x[0] for x in funcs]
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
    iat={i.address:m.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for m in pe.DIRECTORY_ENTRY_IMPORT for i in m.imports if i.name}
    sites=[]
    for rva,name in target:
        i=bisect_right(begins,rva)-1
        end=funcs[i][1] if i>=0 and rva<funcs[i][1] else rva+128
        if not ("PopulateVectorArt@BEE_VectorStream@@" in name or "GetVectorArt@BEE_VectorLayer@@" in name):continue
        calls=[]
        for x in md.disasm(raw[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(rva)+(end-rva)],base+rva):
            if x.mnemonic not in ("call","jmp"):continue
            t=None
            if x.operands:
                o=x.operands[0]
                if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP:t=x.address+x.size+o.mem.disp
                elif o.type==X86_OP_IMM:t=o.imm
            calls.append({"at_rva":hex(x.address-base),"call":iat.get(t,"") or exp.get(t-base,"") if t is not None else "",
                          "operand":x.op_str})
        sites.append({"name":name,"rva":hex(rva),"end_rva":hex(end),"function_bytes":end-rva,"callsite_count":len(calls),"calls":calls})
    out[ver]={"sha256":hashlib.sha256(raw).hexdigest(),"selected_export_list":[{"rva":hex(r),"name":n} for r,n in target],
              "eval_callsite_functions":sites}
    print("==",ver,"selected symbols",len(target),flush=True)
    for fn in sites:
        print(fn["name"][:85],fn["rva"],"size",fn["function_bytes"],"calls",fn["callsite_count"],flush=True)
        for c in fn["calls"]:
            if c["call"]:print(" ",c["at_rva"],c["call"][:130],flush=True)
dst=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-stream-populate-dispatch-2025-2026.json")
dst.write_text(json.dumps({"evidence":"E2-L static code callsite and symbol inventory; no runtime evaluation","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dst)
