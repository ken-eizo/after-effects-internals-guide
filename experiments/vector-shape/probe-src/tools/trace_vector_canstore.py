"""Disassemble native Shape Contents CanStore admission predicates offline."""
from pathlib import Path
import pefile,subprocess,re,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
from bisect import bisect_right
dirs={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files",
      "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files"}
want={"BEE.dll":["CanStore@VectorsStreamGroup@BEE_VectorStream@@"],
      "TDB.dll":["CanStore@TDB_StreamGroup@@","RegisterFactoryFunc@TDB_StreamFactory@@"]}
rx=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
out={}
for ver,root in dirs.items():
    out[ver]={}
    for dll,terms in want.items():
        p=Path(root)/dll;blob=p.read_bytes();pe=pefile.PE(data=blob);base=pe.OPTIONAL_HEADER.ImageBase
        exp={}
        for s in subprocess.run(["dumpbin","/exports",str(p)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
            m=rx.match(s)
            if m:exp[int(m.group(3),16)]=m.group(4)
        rv=sorted(exp)
        imports={i.address:part.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for part in pe.DIRECTORY_ENTRY_IMPORT for i in part.imports if i.name}
        md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
        results=[]
        for addr,name in exp.items():
            if not any(term in name for term in terms):continue
            j=bisect_right(rv,addr);sz=min(1100,max(16,rv[j]-addr if j<len(rv) else 1100))
            off=pe.get_offset_from_rva(addr)
            ops=[]
            for i,x in enumerate(md.disasm(blob[off:off+sz],base+addr)):
                if i>=230:break
                tar=None
                if x.mnemonic in ("call","jmp") and x.operands:
                    z=x.operands[0]
                    if z.type==X86_OP_MEM and z.mem.base==X86_REG_RIP:tar=x.address+x.size+z.mem.disp
                    elif x.op_str.startswith("0x"):
                        try:tar=int(x.op_str,16)
                        except ValueError:pass
                ops.append({"offset":hex(x.address-base),"instruction":x.mnemonic+" "+x.op_str,
                            "callee":imports.get(tar,"") or (exp.get(tar-base,"") if tar is not None else "")})
            results.append({"rva":hex(addr),"name":name,"operations":ops})
        out[ver][dll]=results
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-tdb-vector-canstore-disasm-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L; no private invocation","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for v,a in out.items():
    print("==",v)
    for dll,arr in a.items():
        for r in arr:
            print(dll,r["name"][:85],r["rva"],len(r["operations"]))
            for ins in r["operations"][:65]:
                print(" ",ins["offset"],ins["instruction"],ins["callee"][:110])
print("saved",dest)
