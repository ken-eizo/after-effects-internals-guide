"""Direct, RIP relative executable references to native BEE Vector stream creator functions.
No Adobe code executed. Scan 2 installed version binaries. Code xref != runtime call proof.
"""
from pathlib import Path
from bisect import bisect_right
import re,json,subprocess,pefile,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
bins={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
regex=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
rip=re.compile(r"\[rip ([+-]) (0x[0-9a-fA-F]+)\]")
result={}
for version,path in bins.items():
    blob=path.read_bytes();pe=pefile.PE(data=blob)
    base=pe.OPTIONAL_HEADER.ImageBase
    exp={}
    for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
        m=regex.match(line)
        if m:exp[int(m.group(3),16)]=m.group(4)
    sorted_exports=sorted(exp)
    targets={r:n for r,n in exp.items() if
             ("?Create@" in n and "@BEE_VectorStream@@" in n and
              "SAPEAVTDB_StreamBase" in n) or
             "?Create@BEE_VectorLayer@@" in n}
    hits={k:[] for k in targets}
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.skipdata=True
    examined=0
    for section in pe.sections:
        if not (section.Characteristics & 0x20000000):continue
        for ins in md.disasm(section.get_data(),base+section.VirtualAddress):
            examined+=1
            dst=None
            if ins.mnemonic in ("lea","mov","call","jmp"):
                m=rip.search(ins.op_str)
                if m:
                    disp=int(m.group(2),16)*(1 if m.group(1)=="+" else -1)
                    dst=ins.address+ins.size+disp-base
                elif ins.mnemonic in ("call","jmp") and ins.op_str.startswith("0x"):
                    try:dst=int(ins.op_str,16)-base
                    except ValueError:pass
            if dst in targets:
                idx=bisect_right(sorted_exports,ins.address-base)-1
                near=exp[sorted_exports[idx]] if idx>=0 else ""
                hits[dst].append({"source_rva":hex(ins.address-base),"mnemonic":ins.mnemonic,
                                  "operand":ins.op_str,"nearest_export_not_real_function_boundary":near})
    result[version]={"BEE_sha256":hashlib.sha256(blob).hexdigest(),
                      "instructions_examined":examined,
                      "functions":[{"rva":hex(r),"export":n,"static_refs":hits[r]} for r,n in targets.items()]}
    print("DONE",version,"instructions",examined,"functions",len(targets),"refs",sum(len(x) for x in hits.values()),flush=True)
out=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-stream-creators-static-xrefs-2025-2026.json")
out.write_text(json.dumps({"evidence":"E2-L; static direct call or RIP-relative reference only","versions":result,
"warning":"nearest export is a location hint only; inferred function boundary/retention and caller are not proven"},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for v,sec in result.items():
    print("==",v)
    for c in sec["functions"]:
        if c["static_refs"]:
            print(c["export"].split("@")[0],c["rva"],"refs",len(c["static_refs"]))
            for x in c["static_refs"][:5]:
                print(" ",x["source_rva"],x["mnemonic"],x["nearest_export_not_real_function_boundary"][:125])
print("SAVED",out)
