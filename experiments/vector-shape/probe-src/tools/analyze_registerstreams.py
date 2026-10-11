"""Offline static call-site sampling of layer-specific RegisterStreams.
Disassembly snippets not function-complete CFG; no AE code invocation.
"""
from pathlib import Path
from hashlib import sha256
from capstone import Cs,CS_ARCH_X86,CS_MODE_64,CS_GRP_CALL
import pefile,subprocess,re,json,bisect
targets={
"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")
}
needles=["RegisterStreams@BEE_VectorLayer@@","RegisterStreams@BEE_TextLayer@@",
         "RegisterStreams@BEE_Layer@@", "RegisterStreams@BEE_AVLayer@@",
         "RegisterStreams@BEE_CameraLayer@@", "RegisterStreams@BEE_ModelLayer@@"]
outputs={}
matcher=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
for v,p in targets.items():
    raw=p.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
    result=subprocess.run(["dumpbin","/exports",str(p)],capture_output=True,text=True,errors="replace",check=True)
    names={}
    for line in result.stdout.splitlines():
        m=matcher.match(line)
        if m:names[int(m.group(3),16)]=m.group(4)
    sorted_rva=sorted(names)
    output={}
    for needle in needles:
        match=[(r,n) for r,n in names.items() if needle in n]
        for rva,name in match:
            start=pe.get_offset_from_rva(rva)
            next_idx=bisect.bisect_right(sorted_rva,rva)
            next_rva=sorted_rva[next_idx] if next_idx<len(sorted_rva) else rva+2048
            # Bound to function's next exported RVA and 4096 bytes.
            byte_limit=min(4096,max(0,next_rva-rva))
            code=raw[start:start+byte_limit]
            calls=[];insns=[];count=0
            for inst in md.disasm(code,base+rva):
                count+=1
                if len(insns)<100:insns.append(f"{inst.address:X} {inst.mnemonic} {inst.op_str}")
                if inst.group(CS_GRP_CALL):
                    dst=""
                    if inst.op_str.startswith("0x"):
                        try:
                            call_rva=int(inst.op_str,16)-base
                            dst=names.get(call_rva,"")
                        except ValueError:pass
                    calls.append({"address":hex(inst.address-base),"operand":inst.op_str,
                                  "resolved_export_target":dst[:180]})
            output[needle]={"rva":hex(rva),"export":name,"scan_bytes":byte_limit,
                            "instructions_seen":count,"calls":calls,"first_instructions":insns}
    outputs[v]={"sha256":sha256(raw).hexdigest(),"source_path":str(p),"functions":output}
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-registerstreams-static-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L", "limits":"static disassembly only, not complete CFG, unresolved indirect calls; no public extension authorization","versions":outputs},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("WROTE",dest)
for ver,data in outputs.items():
    print("VERSION",ver)
    for name,x in data["functions"].items():
        print("  ",name, "rva",x["rva"],"insns",x["instructions_seen"],"calls",len(x["calls"]),"scan_bytes",x["scan_bytes"])
        for call in x["calls"][:10]:print("      ",call["address"],call["operand"],call["resolved_export_target"][:85])
