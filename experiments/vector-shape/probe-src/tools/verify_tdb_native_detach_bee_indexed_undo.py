"""F-VECTOR-099: Native TDB detach/parent pointer + BEE structural Undo command
chain on original installed AE2025/2026 DLLs. Read-only, no private ABI call.
"""
from pathlib import Path
import hashlib,json,re,subprocess
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
BINARIES={
"2025":{
"TDB":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
"BEE":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"},
"2026":{
"TDB":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll",
"BEE":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"},
}
PIN={
"2025":{"TDB":"2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69",
"BEE":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730"},
"2026":{"TDB":"82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b",
"BEE":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e"},
}
RX=re.compile(r"^\s*\d+\s+[a-fA-F0-9]+\s+([a-fA-F0-9]{8})\s+(\S+)")
def read(year,mod):
    path=Path(BINARIES[year][mod]);raw=path.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==PIN[year][mod],f"Original {mod} {year} SHA changed; abort"
    pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
    rawexports=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,
                              errors="replace",check=True).stdout
    exports={int(m.group(1),16):m.group(2) for l in rawexports.splitlines() if (m:=RX.match(l))}
    iat={j.address-base:(e.dll.decode(errors="replace").lower(),
                         j.name.decode(errors="replace") if j.name else "")
         for e in pe.DIRECTORY_ENTRY_IMPORT for j in e.imports}
    pdata={z.struct.BeginAddress:z.struct.EndAddress for z in pe.DIRECTORY_ENTRY_EXCEPTION}
    return dict(pe=pe,base=base,exports=exports,iat=iat,pdata=pdata,sha=digest)
def symbol(o,prefix):
    matches=[(a,n) for a,n in o["exports"].items() if n.startswith(prefix)]
    if len(matches)>1: matches=[x for x in matches if "QEAA" in x[1]]
    assert len(matches)==1,(prefix,len(matches))
    return matches[0][0]
def code(o,func):
    a=symbol(o,func);end=o["pdata"].get(a,a+32)
    assert 0<end-a<12000,(func,hex(end-a))
    cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
    out=list(cs.disasm(o["pe"].get_data(a,end-a),o["base"]+a))
    assert out and out[0].address-o["base"]==a
    return a,out
def targets(o,z):
    res=[]
    for arg in z.operands:
        if arg.type==X86_OP_IMM and z.mnemonic in ("call","jmp"):
            res.append(arg.imm-o["base"])
        if arg.type==X86_OP_MEM and arg.mem.base==X86_REG_RIP:
            res.append(z.address+z.size+arg.mem.disp-o["base"])
    return res
def calls(o,ops,a):
    return [z for z in ops if z.mnemonic=="call" and a in targets(o,z)]
def imported(o,ops,mod,prefix):
    return [z for z in ops if z.mnemonic=="call" and any(
        o["iat"].get(t,("",""))[0]==mod and
        o["iat"][t][1].startswith(prefix) for t in targets(o,z))]
def only(xs,context):
    assert len(xs)==1,(context,len(xs),[hex(v.address) for v in xs[:10]])
    return xs[0]
def at(o,x):return hex(x.address-o["base"])
out={}
for year in ("2025","2026"):
    t=read(year,"TDB");b=read(year,"BEE")
    _,parent=code(t,"?SetParent@TDB_StreamBase@@")
    parent_write=only([z for z in parent if z.mnemonic=="mov" and z.op_str=="qword ptr [rcx + 0x20], rdx"],"SetParent parent field")
    rva,detach=code(t,"?RemoveStream@TDB_IndexedStreamGroup@@")
    getcount=only([z for z in detach if z.mnemonic=="call" and z.op_str=="qword ptr [rax + 0x168]"],"GetNumStreams")
    getchild=only([z for z in detach if z.mnemonic=="call" and z.op_str=="qword ptr [rax + 0x178]"],"GetStream")
    holder=only([z for z in detach if z.mnemonic=="mov" and z.op_str=="r14, rax"],"Retained detached child")
    # Number of elements in vector drops by sizeof(pointer).
    shorten=only([z for z in detach if z.mnemonic=="add" and re.fullmatch(r"qword ptr \[(?:rbx|rdi) \+ 0x228\], -8",z.op_str)],"Shrink child list")
    rev=symbol(t,"?UpdateReverseIndexVector@TDB_IndexedStreamGroup@@")
    revcall=only(calls(t,detach,rev),"Reverse index update")
    parentclear=only([z for z in detach if z.mnemonic=="mov" and z.op_str=="qword ptr [r14 + 0x20], 0"],"Detach parent pointer")
    returnchild=only([z for z in detach if z.mnemonic=="mov" and z.op_str=="rax, r14"],"Return original child")
    assert getcount.address<getchild.address<holder.address<shorten.address<revcall.address<parentclear.address<returnchild.address
    assert parent_write.op_str=="qword ptr [rcx + 0x20], rdx"

    # BEE command Add creates a native Stream before marshaling to an undoable command.
    basecreate,baseops=code(t,"?CreateStream@TDB_StreamBase@@")
    fac=symbol(t,"?CreateStream@TDB_StreamFactory@@")
    delegation=only([z for z in baseops if z.mnemonic=="jmp" and fac in targets(t,z)],"StreamBase delegates to registered factory")
    assert delegation.address-baseops[0].address < 48
    start=symbol(b,"?BEE_StartGroupWithNameFromStreamOperation@@")
    execute=symbol(b,"?BEE_DoCommand@@YAHAEAVBEE_UndoContext@@")
    end=symbol(b,"?BEE_EndGroup@@")
    getctx=symbol(b,"?GetUndoContext@BEE_Layer@@")
    operations={
      "add":"?BEE_CmdAddToIndexedStreamGroup@@",
      "remove":"?BEE_CmdRemoveIndexedGroupEntry@@",
      "duplicate":"?BEE_CmdDuplicateIndexedGroupEntry@@",
      "reorder":"?BEE_CmdReorderIndexedGroupEntry@@",
    }
    receipts={}
    for op,prefix in operations.items():
        entry,body=code(b,prefix)
        ctx=calls(b,body,getctx)
        startcall=only(calls(b,body,start),op+" StartGroup")
        run=only(calls(b,body,execute),op+" DoCommand")
        stop=only(calls(b,body,end),op+" EndGroup")
        assert ctx and ctx[0].address<startcall.address<run.address<stop.address,(year,op)
        d=dict(export=b["exports"][entry],entry=hex(entry),
               get_undo_context_sites=[at(b,z) for z in ctx],
               named_undo_group=at(b,startcall),
               command_dispatch=at(b,run),end_group=at(b,stop))
        if op=="add":
            c=only(imported(b,body,"tdb.dll","?CreateStream@TDB_StreamBase@@"),"BEE Add calls TDB StreamBase Creator")
            assert c.address<startcall.address
            d["cross_dll_TDB_StreamBase_CreateStream"]=at(b,c)
        else:
            assert not imported(b,body,"tdb.dll","?CreateStream@TDB_StreamBase@@")
        receipts[op]=d
    out[year]={
      "TDB_sha256":t["sha"],"BEE_sha256":b["sha"],
      "native_stream_base_CreateStream_trampoline":{
        "entry":hex(basecreate),"jmp_factory_CreateStream":at(t,delegation),
        "factory_target":hex(fac)},
      "indexed_detach":{
        "entry_rva":hex(rva),"parent_set_writes_child_plus_0x20":at(t,parent_write),
        "GetNumStreams":at(t,getcount),"GetStream":at(t,getchild),
        "child_reference_retained":at(t,holder),
        "child_vector_length_reduced":at(t,shorten),
        "reverse_index_updated":at(t,revcall),
        "child_parent_field_cleared":at(t,parentclear),
        "same_child_raw_pointer_returned":at(t,returnchild),
        "claim":"Native detach returns existing child pointer; destructor not invoked on shown normal success path"},
      "BEE_indexed_commands":receipts,
      "not_proven":["Undo stored task lifetime or exact inversion implementation",
                    "Detached child's allocator and deletion responsibility of caller",
                    "Successful external native CNL plugin registration",
                    "Thread-safe module unload or persistence"],
    }
    print("PASS",year, "exact parent field +0x20, RemoveStream ownership detach",
          "BEE add/remove/duplicate/reorder commands and TDB factory bridge",flush=True)
    for k,x in receipts.items():
        print(" ",k,x["entry"],x["named_undo_group"],x["command_dispatch"],x["end_group"],flush=True)
dest=ROOT/"datasets"/"ae-tdb-native-detach-bee-command-undo-2025-2026.json"
dest.write_text(json.dumps({"evidence":"E2-L SHA-pinned original installed binary PE static only",
 "proven_product":"Host first-party property structural commands and detach lifetime",
 "external_native_stream_registered":False,"in_host_private_api_called":False,
 "versions":out},indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print("SAVED",dest)
