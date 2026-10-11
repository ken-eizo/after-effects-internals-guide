"""Resolve BEE's direct/indirect import calls into TDB.dll private factory registration.
Offline x64 PE + Capstone, no execution of private code.
"""
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
from bisect import bisect_right
import pefile,subprocess,re,json,hashlib
paths={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files",
       "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files"}
targets=("RegisterStreams@BEE_VectorLayer@@","RegisterStreams@BEE_TextLayer@@","RegisterStreams@BEE_Layer@@",
         "RegisterStreams@BEE_AVLayer@@","??0BEE_VectorLayer@@QEAA@")
rx=re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+(\S+)")
result={}
for v,root in paths.items():
    bin=Path(root)/"BEE.dll";blob=bin.read_bytes();p=pefile.PE(data=blob);base=p.OPTIONAL_HEADER.ImageBase
    imports={}
    for imp in p.DIRECTORY_ENTRY_IMPORT:
        for entry in imp.imports:
            if entry.name:
                imports[entry.address]=imp.dll.decode(errors="replace")+"!"+entry.name.decode(errors="replace")
    s=subprocess.run(["dumpbin","/exports",str(bin)],capture_output=True,text=True,errors="replace",check=True).stdout
    exports={}
    for l in s.splitlines():
        m=rx.match(l)
        if m:exports[int(m.group(3),16)]=m.group(4)
    ordered=sorted(exports)
    decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
    functions=[]
    for rva,name in exports.items():
        if not any(t in name for t in targets):continue
        next_idx=bisect_right(ordered,rva)
        next_rva=ordered[next_idx] if next_idx<len(ordered) else rva+1800
        size=min(max(0,next_rva-rva),6000)
        code=blob[p.get_offset_from_rva(rva):p.get_offset_from_rva(rva)+size]
        calls=[]
        for insn in decoder.disasm(code,base+rva):
            if insn.mnemonic not in ("call","jmp"):continue
            t=None
            if insn.operands and insn.operands[0].type==X86_OP_MEM and insn.operands[0].mem.base==X86_REG_RIP:
                t=insn.address+insn.size+insn.operands[0].mem.disp
            elif insn.op_str.startswith("0x"):
                try:t=int(insn.op_str,16)
                except ValueError:pass
            calls.append({"at_rva":hex(insn.address-base),"mnemonic":insn.mnemonic,
                          "instruction":insn.op_str,
                          "imported":imports.get(t,""),"same_module_export":exports.get(t-base,"") if t is not None else ""})
        functions.append({"rva":hex(rva),"name":name,"size_scanned":size,"calls":calls})
    result[v]={"BEE_sha256":hashlib.sha256(blob).hexdigest(),"TDB_import_count":sum("TDB.dll!" in x for x in imports.values()),
               "functions":functions}
target=Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-bee-registerstreams-iat-targets-2025-2026.json")
target.write_text(json.dumps({"classification":"E2-L", "scope":"bounded disassembly with PE IAT resolved; not dynamic execution", "versions":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for v,r in result.items():
    print("\n==",v)
    for fn in r["functions"]:
        print(fn["name"][:65],fn["rva"],"scanned",fn["size_scanned"],"calls",len(fn["calls"]))
        for x in fn["calls"][:25]:
            print(" ",x["at_rva"],x["imported"][:145] or x["same_module_export"][:145] or x["instruction"])
print("SAVED",target)
