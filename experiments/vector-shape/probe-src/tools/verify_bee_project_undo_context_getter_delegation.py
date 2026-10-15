"""F-VECTOR-103 strict SHA-pinned static x64 BEE Project/Item/Layer UndoContext access chain.
Never loads or executes Adobe DLL; no project/host interaction.
"""
from pathlib import Path
import pefile,capstone,hashlib,subprocess,re,json
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
VERS={
 "2025":{"path":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
         "sha":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730",
         "project_offset":0x368,"layer_item_offset":0x2B8},
 "2026":{"path":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
         "sha":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e",
         "project_offset":0x370,"layer_item_offset":0x260},
}
PART={
 "project":"?GetUndoContext@BEE_Project@@QEAAAEAVBEE_UndoContext@@XZ",
 "item":"?GetUndoContext@BEE_Item@@QEAAAEAVBEE_UndoContext@@XZ",
 "layer":"?GetUndoContext@BEE_Layer@@QEAAAEAVBEE_UndoContext@@XZ",
 "project_const":"?GetUndoContext@BEE_Project@@QEBAAEBVBEE_UndoContext@@XZ",
 "item_const":"?GetUndoContext@BEE_Item@@QEBAAEBVBEE_UndoContext@@XZ",
 "layer_const":"?GetUndoContext@BEE_Layer@@QEBAAEBVBEE_UndoContext@@XZ",
 "get_parent":"?GetParentProject@BEE_Item@@QEAAAEAPEAVBEE_Project@@XZ",
 "project_destructor":"??1BEE_Project@@UEAA@XZ",
 "undo_context_destructor":"??1BEE_UndoContext@@QEAA@XZ",
}
rx=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
def one(xs,why):
    assert len(xs)==1,(why,len(xs),[(hex(x.address),x.op_str) for x in xs[:4]])
    return xs[0]
def calls(ops,rva,b):
    return [i for i in ops if i.mnemonic in ("jmp","call") and i.operands and
            i.operands[0].type==X86_OP_IMM and i.operands[0].imm-b==rva]
res={}
for year,c in VERS.items():
    f=Path(c["path"]);data=f.read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert digest==c["sha"],("BEE.dll changed",year,digest)
    pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
    raw=subprocess.run(["dumpbin","/exports",str(f)],text=True,capture_output=True,check=True,
                       errors="replace").stdout
    syms={int(m.group(1),16):m.group(2) for line in raw.splitlines() if (m:=rx.match(line))}
    def exp(name):
        a=[r for r,s in syms.items() if s==name];assert len(a)==1,(year,name,len(a))
        return a[0]
    r={n:exp(v) for n,v in PART.items()}
    pdata={x.struct.BeginAddress:x.struct.EndAddress for x in pe.DIRECTORY_ENTRY_EXCEPTION}
    def func(n):
        a=r[n];end=min(pdata.get(a,a+32),a+200)
        z=list(cs.disasm(pe.get_data(a,end-a),base+a))
        for index, instr in enumerate(z):
            if instr.mnemonic in ("ret","jmp"):
                return z[:index+1]
        raise AssertionError((year,n,"expected terminating ret/jmp"))
    evidence={}
    for tag in ("project","item","layer","project_const","item_const","layer_const"):
        zz=func(tag);a=r[tag]
        assert zz and zz[0].address-base==a
        if tag.startswith("project"):
            off=c["project_offset"]
            x=one([i for i in zz if i.mnemonic=="mov" and i.op_str==f"rax, qword ptr [rcx + 0x{off:x}]"],tag+" project field")
            y=one([i for i in zz if i.mnemonic=="add" and i.op_str=="rax, 0x10"],tag+" indirect UndoContext subobject")
            ret=one([i for i in zz if i.mnemonic=="ret" and y.address<i.address<y.address+10],tag+" return")
            evidence[tag]={"entry":hex(a),"host_project_context_handle_offset":hex(off),
                           "indirect_undo_context_offset":"0x10","field_read":hex(x.address-base)}
        elif tag.startswith("item"):
            m=one([i for i in zz if i.mnemonic=="mov" and i.op_str=="rcx, qword ptr [rcx + 0x38]"],tag+" project field")
            dest=r["project_const" if tag.endswith("_const") else "project"]
            j=one(calls(zz,dest,base),tag+" delegated exact Project getter")
            assert m.address<j.address and j.mnemonic=="jmp"
            evidence[tag]={"entry":hex(a),"item_project_ptr_offset":"0x38",
                           "delegates_to_project_getter":hex(dest)}
        else:
            off=c["layer_item_offset"]
            m=one([i for i in zz if i.mnemonic=="mov" and i.op_str==f"rcx, qword ptr [rcx + 0x{off:x}]"],tag+" layer Item ptr")
            call=one([i for i in zz if i.mnemonic=="call" and i.operands[0].type==X86_OP_IMM
                      and i.operands[0].imm-base==r["get_parent"]],tag+" project owner resolution")
            project=one([i for i in zz if i.mnemonic=="mov" and i.op_str=="rcx, qword ptr [rax]"],tag+" deref project")
            dest=r["project"] # Both const and non-const Layer getter dispatch to mutable Project getter in installed BEE.
            j=one(calls(zz,dest,base),tag+" delegated Project getter")
            assert m.address<call.address<project.address<j.address and j.mnemonic=="jmp"
            asserts=[i for i in zz if i.mnemonic=="je" and m.address<i.address<j.address]
            assert len(asserts)==2,(year,tag,len(asserts))
            evidence[tag]={"entry":hex(a),"layer_item_ptr_offset":hex(off),
                 "GetParentProject":hex(r["get_parent"]),
                 "deref_returned_project_ptr":hex(project.address-base),
                 "null_guard_count":2,"delegates_to_project_getter":hex(dest)}
    # The real Project destructor must release the exact context subobject
    # previously returned by the Project getter. This is stronger than
    # an indirect access graph, but still not a live project-close receipt.
    projdtor=r["project_destructor"];end=pdata[projdtor]
    assert 0<end-projdtor<3500
    dd=list(cs.disasm(pe.get_data(projdtor,end-projdtor),base+projdtor))
    off=c["project_offset"]
    load=one([z for z in dd if z.mnemonic=="mov" and z.op_str==f"rdi, qword ptr [rbx + 0x{off:x}]"],"Project dtor context pointer")
    nullcheck=one([z for z in dd if z.mnemonic=="test" and z.op_str=="rdi, rdi"
                   and 0<z.address-load.address<12],"Project dtor null guard")
    context=one([z for z in dd if z.mnemonic=="lea" and z.op_str=="rcx, [rdi + 0x10]"
                 and z.address>nullcheck.address],"Project dtor UndoContext subobject")
    undone=one([z for z in dd if z.mnemonic=="call" and z.operands[0].type==X86_OP_IMM
                and z.operands[0].imm-base==r["undo_context_destructor"]],"Project dtor calls true UndoContext destructor")
    allocsize=one([z for z in dd if z.mnemonic=="mov" and z.op_str=="edx, 0x130"
                   and z.address>undone.address],"Project dtor frees containing context allocation")
    allocator=one([z for z in dd if z.mnemonic=="call" and
                   allocsize.address<z.address<allocsize.address+12],"Project dtor deallocation")
    assert load.address<nullcheck.address<context.address<undone.address<allocsize.address<allocator.address
    dtorinfo={
     "project_destructor_rva":hex(projdtor),
     "context_pointer_load_rva":hex(load.address-base),
     "context_ptr_null_guard_rva":hex(nullcheck.address-base),
     "undo_context_subobject_address_rva":hex(context.address-base),
     "direct_BEE_UndoContext_destructor_call_rva":hex(undone.address-base),
     "undo_context_destructor_rva":hex(r["undo_context_destructor"]),
     "context_allocation_bytes":0x130,
     "deallocation_after_context_destructor_rva":hex(allocator.address-base)}
    res[year]={"original_BEE_sha256":digest,"verified_undo_context_accessors":evidence,
       "verified_project_destruction_calls_undo_context":dtorinfo,
       "scope":"Original installed BEE.dll static only; not a live project-close receipt or evidence of safe foreign plugin unload",
       "foreign_native_type_registered":False}
    print("PASS",year,"Project ProjectHandle +0x10; Item +0x38; Layer -> Item/GetParentProject -> Project UndoContext; two guarded null branches")
    print("  project ptr offset",hex(c["project_offset"]),"layer Item ptr offset",hex(c["layer_item_offset"]),
          "Project::~ UndoContext::~",hex(undone.address-base),flush=True)
out=Path(__file__).resolve().parents[4] / "datasets" / "ae-bee-project-undo-context-getter-delegation-2025-2026.json"
out.write_text(json.dumps({"evidence":"E2-L original SHA pinned AE2025/2026 BEE.dll x64 direct getter chain",
 "versions":res},indent=2)+"\n",encoding="utf8")
print("SAVED",out)
