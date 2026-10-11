"""Offline TDB factory ABI audit; no host-side private calls.
Use x64 .pdata function boundaries, export names and PE import table.
"""
from pathlib import Path
from bisect import bisect_right
import pefile, subprocess, re, json, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP, X86_OP_IMM
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
BIN={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll")}
NAMES=["RegisterFactoryFunc@TDB_StreamFactory@@","CreateStream@TDB_StreamFactory@@",
"GetCanonicalInstance@TDB_StreamFactory@@","GetCanonicalStream@TDB_StreamFactory@@",
"RegisterCanonicalInstance@TDB_StreamFactory@@","UnregisterFactoryFunc@TDB_StreamFactory@@",
"UnregisterAll@TDB_ScRegisterStreams@@","Register@TDB_ScRegisterStreams@@",
"MakeInstanceFromCanonical@TDB_StreamFactory@@",
"Get_AE_StreamFactory@@","RegisterSeparatedDimensions@TDB_StreamFactory@@"]
RX=re.compile(r"^\s*(\d+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]{8})\s+(\S+)")
out={}
for ver,path in BIN.items():
    raw=path.read_bytes()
    pe=pefile.PE(data=raw)
    base=pe.OPTIONAL_HEADER.ImageBase
    exports={}
    for l in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
        m=RX.match(l)
        if m:exports[int(m.group(3),16)]=m.group(4)
    iat={ent.address: mod.dll.decode(errors="replace")+"!"+ent.name.decode(errors="replace") for mod in pe.DIRECTORY_ENTRY_IMPORT for ent in mod.imports if ent.name}
    unwind=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
    starts=[x[0] for x in unwind]
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
    details=[]
    for addr,name in exports.items():
        if not any(t in name for t in NAMES):continue
        k=bisect_right(starts,addr)-1
        bound=unwind[k][1] if k>=0 and addr<unwind[k][1] else addr+128
        size=min(bound-addr,18000)
        region=raw[pe.get_offset_from_rva(addr):pe.get_offset_from_rva(addr)+size]
        instructions=[]
        for ins in md.disasm(region,base+addr):
            target=None
            if ins.operands and ins.mnemonic in ("call","jmp"):
                a=ins.operands[0]
                if a.type==X86_OP_MEM and a.mem.base==X86_REG_RIP:target=ins.address+ins.size+a.mem.disp
                elif a.type==X86_OP_IMM:target=a.imm
            if ins.mnemonic in ("call","jmp","ret","cmp","test","je","jne","jb","ja","jz","jnz","cmovne","cmove") or (ins.mnemonic=="mov" and "[r13 +" in ins.op_str):
                instructions.append({"rva":hex(ins.address-base),"op":ins.mnemonic,"args":ins.op_str,
                                     "callee":iat.get(target,"") or (exports.get(target-base,"") if target is not None else "")})
        details.append({"name":name,"rva":hex(addr),"function_end":hex(bound),"scanned_bytes":size,"instructions":instructions})
    out[ver]={"TDB_sha256":hashlib.sha256(raw).hexdigest(),"entries":details}
    print("\n====",ver,"methods",len(details),flush=True)
    for m in details:
        ct=sum(x["op"]=="call" for x in m["instructions"])
        print(m["name"].split("@")[0],m["rva"],"bytes",m["scanned_bytes"],"calls",ct,flush=True)
        for ins in m["instructions"]:
            if ins["op"]=="call":
                print(" ",ins["rva"],ins["callee"][:125] or ins["args"],flush=True)
dst=ROOT/"datasets"/"ae-tdb-factory-lifetime-canonical-controlflow-2025-2026.json"
dst.write_text(json.dumps({"classification":"E2-L disassembly, no private calls, not ABI stability guarantee","versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dst,flush=True)
