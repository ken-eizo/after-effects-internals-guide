"""Cross-version direct xrefs for AE vector edit selection and render-origin identity.
No private API calls or running host changes; direct CALL/JMP are incomplete.
"""
from pathlib import Path
from hashlib import sha256
from bisect import bisect_right
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
import re,subprocess,pefile,json
bins={"AE2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
      "AE2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
needles=[
"?BEE_GetSelectedShapePathsVec@@","IsPathOrChildSelected@BEE_SelLayer@@",
"GetStreamIDPath@OriginInfo@BEE_VectorArt@@","GetCompletePath@OriginInfo@BEE_VectorArt@@",
"AppendSyntheticIndex@OriginInfo@BEE_VectorArt@@","LayerSelectSetupPrePlayback@C_AGMDLTranslatePort@@",
"PopulateVectorArt@BEE_VectorStream@@","GetVectorArt@BEE_VectorLayer@@","GetBounds@BEE_VectorArt@@"]
regex=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
result={}
for label,path in bins.items():
    raw=path.read_bytes(); p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
    cp=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True)
    exports={}
    for row in cp.stdout.splitlines():
        m=regex.match(row)
        if m:exports[int(m.group(3),16)]=m.group(4)
    ordered=sorted(exports)
    targets={r:name for r,name in exports.items() if any(q in name for q in needles)}
    refs={name:[] for name in targets.values()}
    engine=Cs(CS_ARCH_X86,CS_MODE_64);engine.skipdata=True
    decoded=0
    for sect in p.sections:
        if not (sect.Characteristics&0x20000000):continue
        for inst in engine.disasm(sect.get_data(),base+sect.VirtualAddress):
            decoded+=1
            if inst.mnemonic not in ("call","jmp") or not inst.op_str.startswith("0x"):continue
            try:target=int(inst.op_str,16)-base
            except ValueError:continue
            if target not in targets:continue
            owner_i=bisect_right(ordered,inst.address-base)-1
            approx=exports[ordered[owner_i]] if owner_i>=0 else ""
            refs[targets[target]].append({"callsite_rva":hex(inst.address-base),"mnemonic":inst.mnemonic,
                                         "nearest_preceding_export":approx[:350]})
    result[label]={"binary_sha256":sha256(raw).hexdigest(),"decoded_instructions":decoded,
                   "method_refs":{name:{"method_rva":hex(r),"count":len(refs[name]),
                                         "references":refs[name][:250]} for r,name in targets.items()}}
dest=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-selection-origin-xrefs-2025-2026.json")
dest.write_text(json.dumps({"evidence":"E2-L static direct references only; virtual and indirect calls invisible",
                            "warning":"nearest preceding export is not reliable real caller function boundary",
                            "binaries":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for v,data in result.items():
    print("==",v,"instructions",data["decoded_instructions"])
    for name,rows in data["method_refs"].items():
        print(" ",name[:70],"XREF",rows["count"])
        for r in rows["references"][:4]:print("   ",r["callsite_rva"],r["nearest_preceding_export"][:110])
print("SAVED",dest)
