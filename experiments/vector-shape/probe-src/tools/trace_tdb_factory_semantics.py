"""Focused disassembly receipts for BEE register dispatcher and TDB factories.
No private code executed. Bound to next export and 1000 instructions.
"""
from pathlib import Path
import pefile,subprocess,re,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
from bisect import bisect_right
directories={
"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files"}
targets={"BEE.dll":["RegisterStreams@BEE_Layer@@","RegisterStreams@BEE_VectorLayer@@"],
         "TDB.dll":["Get_AE_StreamFactory@@","RegisterFactoryFunc@TDB_StreamFactory@@",
                    "Register@TDB_ScRegisterStreams@@","UnregisterAll@TDB_ScRegisterStreams@@",
                    "CreateStream@TDB_StreamFactory@@"]}
rx=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
out={}
for version,dr in directories.items():
    out[version]={}
    for dll,substrings in targets.items():
        p=Path(dr)/dll
        raw=p.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
        symbols={}
        for l in subprocess.run(["dumpbin","/exports",str(p)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
            m=rx.match(l)
            if m:symbols[int(m.group(3),16)]=m.group(4)
        order=sorted(symbols)
        imports={}
        for m in pe.DIRECTORY_ENTRY_IMPORT:
            for it in m.imports:
                if it.name:imports[it.address]=m.dll.decode(errors="replace")+"!"+it.name.decode(errors="replace")
        md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
        samples=[]
        for rva,name in symbols.items():
            if not any(x in name for x in substrings):continue
            nxt=bisect_right(order,rva)
            sz=min(1800,max(40,order[nxt]-rva if nxt<len(order) else 1800))
            start=pe.get_offset_from_rva(rva)
            instructions=[]
            for i,x in enumerate(md.disasm(raw[start:start+sz],base+rva)):
                if i>=260:break
                target=None
                if x.mnemonic in ("call","jmp") and x.operands:
                    if x.operands[0].type==X86_OP_MEM and x.operands[0].mem.base==X86_REG_RIP:
                        target=x.address+x.size+x.operands[0].mem.disp
                    elif x.op_str.startswith("0x"):
                        try:target=int(x.op_str,16)
                        except ValueError:pass
                instructions.append({"rva":hex(x.address-base),"op":x.mnemonic,
                                     "operands":x.op_str,
                                     "callee":imports.get(target,"") or symbols.get(target-base,"") if target is not None else ""})
            samples.append({"rva":hex(rva),"name":name,"scan_bytes":sz,"instructions":instructions})
        out[version][dll]={"sha256":hashlib.sha256(raw).hexdigest(),"samples":samples}
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-tdb-register-callsite-disasm-2025-2026.json")
dest.write_text(json.dumps({"classification":"E2-L static disassembly only; no vtable/ownership proofs","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for v,o in out.items():
    print("==",v)
    for dll,info in o.items():
        for s in info["samples"]:
            print(dll,s["name"][:65],"at",s["rva"],"insns",len(s["instructions"]))
            for ins in s["instructions"]:
                if ins["op"] in ("call","jmp"):print("   ",ins["rva"],ins["op"],ins["callee"][:100] or ins["operands"])
print("SAVED",dest)
