"""Offline bounded disassembly of native VectorLayer creation command and constructor.
No host interaction/private calls. Output exact binary hashes and resolved exports.
"""
from pathlib import Path
from bisect import bisect_right
from capstone import Cs,CS_ARCH_X86,CS_MODE_64,CS_GRP_CALL
import subprocess,pefile,re,json,hashlib
binaries={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
          "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
targets=["BEE_CmdNewVectorLayer@@","??0BEE_VectorLayer@@QEAA@","RegisterStreams@BEE_VectorLayer@@",
         "BEE_GetSelectedShapePathsVec@@"]
matcher=re.compile(r"^\s*(\d+)\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
out={}
for version,path in binaries.items():
    content=path.read_bytes(); pe=pefile.PE(data=content);base=pe.OPTIONAL_HEADER.ImageBase
    dump=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True)
    exports={}
    for line in dump.stdout.splitlines():
        m=matcher.match(line)
        if m: exports[int(m.group(2),16)]=m.group(3)
    order=sorted(exports)
    scanner=Cs(CS_ARCH_X86,CS_MODE_64)
    findings=[]
    for query in targets:
        for rva,name in exports.items():
            if query not in name:continue
            idx=bisect_right(order,rva)
            next_rva=order[idx] if idx<len(order) else rva+4096
            limit=min(4096,max(16,next_rva-rva))
            code=content[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(rva)+limit]
            calls=[];first=[]
            for i,inst in enumerate(scanner.disasm(code,base+rva)):
                if i<45:first.append(f"{inst.address-base:08X} {inst.mnemonic} {inst.op_str}")
                if inst.mnemonic in ("call","jmp"):
                    target=None
                    if inst.op_str.startswith("0x"):
                        try: target=int(inst.op_str,16)-base
                        except ValueError: pass
                    calls.append({"site_rva":hex(inst.address-base),"operand":inst.op_str,
                                  "target_export":exports.get(target,"")[:350]})
            findings.append({"export_name":name,"rva":hex(rva),"bytes_scanned":limit,
                             "first_instructions":first,"calls_or_jmps":calls[:90]})
    out[version]={"source":str(path),"sha256":hashlib.sha256(content).hexdigest(),"functions":findings}
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-layer-construction-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L static disassembly","limits":"no runtime proof, unresolved indirect calls; export-boundary heuristic","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for ver,o in out.items():
    print("====",ver)
    for fn in o["functions"]:
        print(fn["rva"],fn["export_name"][:145],"calls",len(fn["calls_or_jmps"]))
        for c in fn["calls_or_jmps"][:14]:print("   ",c["site_rva"],c["operand"],c["target_export"][:110])
print("SAVED",dest)
