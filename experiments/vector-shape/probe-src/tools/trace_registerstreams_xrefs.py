"""PE executable-section direct call-target xref inventory for shape-related functions.
Use native Capstone decoding, not a raw E8 substring scan. Direct calls only.
Does not prove runtime invocation or private ABI usability.
"""
from pathlib import Path
from hashlib import sha256
from bisect import bisect_right
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
import re,subprocess,pefile,json,time
versions={
"AE2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
"AE2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
pattern=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
needles=("RegisterStreams@BEE_VectorLayer@@","RegisterStreams@BEE_TextLayer@@",
         "RegisterStreams@BEE_Layer@@","RegisterStreams@BEE_AVLayer@@",
         "PopulateVectorArt@BEE_VectorStream@@", "Rasterize2DGraph@BEE_VectorLayer@@")
output={}
for label,path in versions.items():
    start=time.perf_counter()
    raw=path.read_bytes(); pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
    dump=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,
                        text=True,errors="replace",check=True).stdout
    exports={}
    for line in dump.splitlines():
        m=pattern.match(line)
        if m:exports[int(m.group(3),16)]=m.group(4)
    rvas=sorted(exports)
    targets={r:name for r,name in exports.items() if any(token in name for token in needles)}
    hits={name:[] for name in targets.values()}
    md=Cs(CS_ARCH_X86,CS_MODE_64)
    md.skipdata=True  # Embedded data must not prematurely terminate the section scan.
    decoded=0
    for section in pe.sections:
        if not (section.Characteristics&0x20000000):continue
        data=section.get_data()
        for inst in md.disasm(data,base+section.VirtualAddress):
            decoded+=1
            if inst.mnemonic not in ("call","jmp") or not inst.op_str.startswith("0x"):
                continue
            try:
                target_rva=int(inst.op_str,16)-base
            except ValueError:continue
            if target_rva not in targets:continue
            owner_i=bisect_right(rvas,inst.address-base)-1
            estimated_owner=exports[rvas[owner_i]] if owner_i>=0 else ""
            hits[targets[target_rva]].append({
                "callsite_rva":hex(inst.address-base),"instruction":inst.mnemonic,
                "nearest_preceding_export":estimated_owner[:240],
                "nearest_preceding_export_rva":hex(rvas[owner_i]) if owner_i>=0 else ""})
    output[label]={
        "source_binary":str(path),"binary_sha256":sha256(raw).hexdigest(),
        "decoded_executable_section_instructions":decoded,
        "elapsed_seconds":round(time.perf_counter()-start,2),
        "target_direct_xrefs":{name:{"target_rva":hex(r),"count":len(hits[name]),"sites":hits[name][:100]} for r,name in targets.items()}
    }
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-registerstreams-xrefs-2025-2026.json")
dest.write_text(json.dumps({"classification":"E2-L static direct xrefs; indirect calls omitted; approximate owner labels",
                            "note":"Nearest preceding *export* is not always the real containing function.",
                            "data":output},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
for v,o in output.items():
    print(v,o["decoded_executable_section_instructions"],"insns",o["elapsed_seconds"],"seconds")
    for name,refs in o["target_direct_xrefs"].items():
        print(" ",name[:70],refs["target_rva"],"calls",refs["count"])
        for r in refs["sites"][:5]:print("    ",r["callsite_rva"],r["nearest_preceding_export"][:145])
print("WROTE",dest)
