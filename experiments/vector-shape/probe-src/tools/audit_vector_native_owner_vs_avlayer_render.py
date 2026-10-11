"""EXP-SHAPE-023: class factory, layer owner and native vector render dispatch.
Scoped, offline, exact installed BEE.dll PE exports and x64 .pdata functions.
Answers: Does native Shape VectorArt/rendering sit behind a concrete layer
virtual method, and what host command constructs that owner?
Never calls/injects any Adobe code or requires AE to be running.
"""
from pathlib import Path
import pefile,subprocess,hashlib,json,re,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP

root=Path(r"D:\Developer\After Effects Internals Guide")
files={"AE2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),
       "AE2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")}
selectors=[
"?Create@BEE_AVLayer@@",
"?Create@BEE_VectorLayer@@",
"?BEE_CmdNewVectorLayer@@",
"?BEE_CmdNewLayer@@",
"?CreateNewLayer@BEE_ModelItem@@",
"?Rasterize2DGraph@BEE_AVLayer@@",
"?Rasterize2DGraph@BEE_VectorLayer@@",
"?GetVectorArt@BEE_VectorLayer@@",
"?GetLayerType@BEE_VectorLayer@@",
"?GetLayerType@BEE_AVLayer@@",
"?GetDefaultTypeMagic@BEE_VectorLayer@@",
"?GetDefaultTypeMagic@BEE_AVLayer@@",
"?InitArtCache@BEE_VectorLayer@@",
"?CanHaveEffects@BEE_VectorLayer@@",
"?CanHaveMasks@BEE_VectorLayer@@",
"?RegisterStreams@BEE_VectorLayer@@",
"?RegisterStreams@BEE_AVLayer@@",
"?BEE_StreamGroupName_VECTOR_LAYER@@",
"?BEE_VectorStream::StreamName_ROOT_VECTORS_GROUP@@"
]
pat=re.compile(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)")
out={}
for version,path in files.items():
    print("START",version,flush=True)
    raw=path.read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
    symbols={}
    cmd=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,
                       text=True,errors="replace",check=True)
    for line in cmd.stdout.splitlines():
        m=pat.match(line)
        if m:symbols[int(m.group(1),16)]=m.group(2)
    imp={entry.address:desc.dll.decode(errors="replace")+"!"+entry.name.decode(errors="replace")
         for desc in p.DIRECTORY_ENTRY_IMPORT for entry in desc.imports if entry.name}
    pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
    starts=[x[0] for x in pdata]
    cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
    records=[]
    for query in selectors:
        entries=[(rva,name) for rva,name in symbols.items() if query in name]
        if not entries:
            records.append({"query":query,"export_found":False});continue
        for rva,symbol in entries:
            row={"query":query,"symbol":symbol,"symbol_rva":hex(rva)}
            index=bisect.bisect_right(starts,rva)-1
            if index<0 or rva>=pdata[index][1]:
                row["function_bounded"]=False;records.append(row);continue
            lo,hi=pdata[index];row.update({"function_bounded":True,"start_rva":hex(lo),"end_rva":hex(hi),
                                          "bytes":hi-lo})
            if hi-lo>400000:
                row["skipped"]="function too large";records.append(row);continue
            instructions=[];calls=[];constants=[]
            for inst in cs.disasm(raw[p.get_offset_from_rva(lo):p.get_offset_from_rva(lo)+(hi-lo)],base+lo):
                if len(instructions)<45:
                    instructions.append({"rva":hex(inst.address-base),"opcode":inst.mnemonic,"operand":inst.op_str})
                if inst.mnemonic in ("call","jmp") and inst.operands:
                    oper=inst.operands[0];target=None
                    if oper.type==X86_OP_IMM:target=oper.imm
                    elif oper.type==X86_OP_MEM and oper.mem.base==X86_REG_RIP:
                        target=inst.address+inst.size+oper.mem.disp
                    calls.append({"rva":hex(inst.address-base),
                                  "target_rva":hex(target-base) if target else None,
                                  "symbol":(symbols.get(target-base) or imp.get(target) or "") if target else "",
                                  "assembly":inst.mnemonic+" "+inst.op_str})
                if inst.operands:
                    for oper in inst.operands:
                        if oper.type==X86_OP_MEM and oper.mem.base==X86_REG_RIP:
                            addr=inst.address+inst.size+oper.mem.disp-base
                            sym=symbols.get(addr,"")
                            if sym:constants.append({"site":hex(inst.address-base),"symbol":sym})
            row.update({"first_instructions":instructions,"call_or_jmp_count":len(calls),
                        "calls":calls,"exported_static_refs":constants})
            records.append(row)
            focused=[c for c in calls if c["symbol"] and any(x in c["symbol"] for x in
                     ["BEE_","TDB_","Stream","Layer","Render","Art","CompItem","Project","BEE"])]
            print(" ",query,"RVA",hex(lo),"BYTES",hi-lo,"calls",len(calls),"named",len(focused),flush=True)
            for c in focused[:50]:print("   ",c["rva"],c["symbol"][:180],flush=True)
    out[version]={"image":str(path),"SHA256":hashlib.sha256(raw).hexdigest(),"results":records}
dest=root/"datasets/ae-vector-layer-native-owner-vs-avlayer-render-2025-2026.json"
dest.write_text(json.dumps({"classification":"E2-L exported/pdata-bounded x64 binary static evidence, not an effect/vector plugin ABI",
  "versions":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
