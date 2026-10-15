"""EXP-SHAPE-102: Strict native indexed Add/Remove reciprocal Undo tasks and Stream lifetime.

Read-only SHA-pinned installed AE2025 and AE2026 BEE.dll original PE.
No private code execution, no host process or project access. Bounded
x64 disassembly + RTTI CompleteObjectLocator + command table + native IAT.
"""
from pathlib import Path
import struct,hashlib,json,pefile,capstone
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
VERSIONS={
"2025":{"path":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"sha":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730",
"table":0xFEC250,"add":70,"remove":72,
"v_add":0xF914B8,"v_remove":0xF914D8,
"owned_flag_offset":0x48,"stream_pointer_offset":0x40,
"add_dtor":0x549C90,"add_replay":0x54C640,"remove_dtor":0x549EE0,"remove_replay":0x54CF00},
"2026":{"path":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
"sha":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e",
"table":0x104C530,"add":71,"remove":73,
"v_add":0xFF0860,"v_remove":0xFF0880,
"owned_flag_offset":0x50,"stream_pointer_offset":0x40,
"add_dtor":0x568A30,"add_replay":0x56B270,"remove_dtor":0x568CB0,"remove_replay":0x56BC10},
}
CS=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);CS.detail=True
def unique(seq,desc):
    assert len(seq)==1,(desc,len(seq),[hex(x.address) for x in seq[:5]])
    return seq[0]
def rva(o,z):return hex(z.address-o["base"])
def load(ver,c):
    data=Path(c["path"]).read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert digest==c["sha"],("Original Adobe BEE.dll SHA mismatch",ver,digest)
    pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
    ends={i.struct.BeginAddress:i.struct.EndAddress for i in pe.DIRECTORY_ENTRY_EXCEPTION}
    imports={i.address-base:(entry.dll.decode(errors="replace").lower(),
                            i.name.decode(errors="replace") if i.name else "")
             for entry in pe.DIRECTORY_ENTRY_IMPORT for i in entry.imports}
    return dict(pe=pe,base=base,ends=ends,imports=imports,sha=digest)
def dis(o,a):
    assert a in o["ends"],("missing native function pdata",hex(a))
    size=o["ends"][a]-a;assert 0<size<16000,(hex(a),size)
    instructions=list(CS.disasm(o["pe"].get_data(a,size),o["base"]+a))
    assert instructions and instructions[0].address==o["base"]+a
    return instructions
def u64(o,a):
    return struct.unpack("<Q",o["pe"].get_data(a,8))[0]
def col_rtti(o,vt):
    base=o["base"];col_va=u64(o,vt-8);a=col_va-base
    assert 0<a<o["pe"].OPTIONAL_HEADER.SizeOfImage
    signature,offset,cdOffset,type_desc,class_desc,self_rva=struct.unpack("<IIIIII",o["pe"].get_data(a,24))
    assert signature==1 and self_rva==a,("Not a PE RTTI COL on x64",hex(vt))
    name=o["pe"].get_data(type_desc+16,150).split(b"\0")[0].decode()
    return name
def rip_target(o,z):
    if z.mnemonic not in ("lea","mov") or not z.operands:return None
    for v in z.operands:
        if v.type==X86_OP_MEM and v.mem.base==X86_REG_RIP:
            return z.address+z.size+v.mem.disp-o["base"]
    return None
def is_imp(o,z,dll,prefix):
    if z.mnemonic!="call" or not z.operands:return False
    v=z.operands[0]
    if v.type!=X86_OP_MEM or v.mem.base!=X86_REG_RIP:return False
    a=z.address+z.size+v.mem.disp-o["base"]
    m,n=o["imports"].get(a,("",""))
    return m==dll and n.startswith(prefix)
def seq_find(seq,mnem,operand):
    return [z for z in seq if z.mnemonic==mnem and z.op_str==operand]

result={}
for ver,c in VERSIONS.items():
    o=load(ver,c);pe=o["pe"];base=o["base"]
    receipts={}
    names={"add":"BEE_DoAddToIndexedStreamGroupTask","remove":"BEE_DoRemoveIndexedGroupTask"}
    for kind,name in names.items():
        idx=c[kind];row=c["table"]+idx*32
        q=struct.unpack("<QQQQ",pe.get_data(row,32))
        strings=q[0]-base
        assert pe.get_data(strings,len(name)+1)==name.encode()+b"\0",(ver,kind)
        assert q[3] != 0, (ver,kind,'command metadata must be present')
        vt=c["v_"+kind]
        assert col_rtti(o,vt)==".?AV"+name+"@@",(ver,kind,col_rtti(o,vt))
        a0=u64(o,vt)-base;a8=u64(o,vt+8)-base
        assert a0==c[kind+"_dtor"] and a8==c[kind+"_replay"],(ver,kind)
        # The first command factory allocates an actual concrete C++ task and invokes constructor.
        factory=q[1]-base;copyfactory=q[2]-base
        f=dis(o,factory);cf=dis(o,copyfactory)
        assert any(z.mnemonic=="mov" and z.op_str.startswith("ecx, 0x") for z in f)
        assert any(z.mnemonic=="call" and z.operands[0].type==X86_OP_IMM for z in f)
        assert len(cf)>5
        receipts[kind]=dict(table_index=idx,table_entry=hex(row),native_command_name=name,
                            class_rtti=col_rtti(o,vt),vtable=hex(vt),
                            factory=hex(factory),copy_factory=hex(copyfactory),
                            virtual_deleting_destructor=hex(a0),virtual_replay=hex(a8))
    add=dis(o,c["add_replay"]);remove=dis(o,c["remove_replay"])
    reciprocal={}
    for origin,code,target_kind in (("add",add,"remove"),("remove",remove,"add")):
        target=c["v_"+target_kind]
        loads=[z for z in code if z.mnemonic=="lea" and z.op_str.startswith("rax, [rip")
               and rip_target(o,z)==target]
        loaded=unique(loads,origin+" loads reciprocal vtable")
        insidx=code.index(loaded)
        store=unique([z for z in code[insidx+1:insidx+4]
                      if z.mnemonic=="mov" and z.op_str=="qword ptr [rbx], rax"],
                    origin+" sets returned opposite task vtable")
        assert loaded.address<store.address
        ret=[z for z in code[insidx:] if z.mnemonic=="ret"]
        assert ret
        # The native task returns a newly constructed inverse instance, not an
        # arbitrary opaque value; output's RBX is moved to RAX on success path.
        returns=[z for z in code[insidx:] if z.mnemonic=="mov" and z.op_str=="rax, rbx"]
        assert returns,(ver,origin,"must return newly created RBX task")
        reciprocal[origin]=dict(task_replay=hex(c[origin+"_replay"]),
             creates_inverse_class=names[target_kind],loads_inverse_vtable=rva(o,loaded),
             stores_inverse_vtable=rva(o,store),returns_created_inverse=rva(o,returns[-1]))
    # Remove execution converts detached Stream to an Add task that OWNS it.
    f=c["owned_flag_offset"]
    owned=unique(seq_find(remove,"mov",f"byte ptr [rbx + 0x{f:x}], 1"),"Remove returns Add with owner flag")
    assert int(reciprocal["remove"]["stores_inverse_vtable"],16)<owned.address-base
    inverse_ptr=[z for z in remove if z.mnemonic=="mov" and
                 z.op_str=="qword ptr [rbx + 0x40], rax"]
    assert len(inverse_ptr)==1 and inverse_ptr[0].address<owned.address

    # Inverse Add deleting destructor conditions: owned, nonnull Stream,
    # noncanonical. If parent attached: virtual RemoveChild and then deletion.
    dtor=dis(o,c["add_dtor"])
    checkflag=unique(seq_find(dtor,"cmp",f"byte ptr [rbx + 0x{f:x}], 0"),"Add owned-state check")
    load_stream=[z for z in dtor if z.mnemonic=="mov" and z.op_str=="rcx, qword ptr [rbx + 0x40]"]
    assert len(load_stream)>=2
    canonical=unique([z for z in dtor if is_imp(o,z,"tdb.dll","?IsCanonical@TDB_StreamBase@@")],"Add destructor IsCanonical")
    parent=unique([z for z in dtor if is_imp(o,z,"tdb.dll","?GetParent@TDB_StreamBase@@")],"Add destructor GetParent")
    assert checkflag.address<canonical.address<parent.address
    if ver=="2025":
        remove_child=unique(seq_find(dtor,"call","r8"),"2025 parent RemoveChild vtable call")
        assert any(z.mnemonic=="mov" and z.op_str=="r8, qword ptr [rcx + 0x1e0]"
                   for z in dtor if z.address<remove_child.address)
    else:
        remove_child=unique(seq_find(dtor,"call","qword ptr [r8 + 0x1e0]"),"2026 parent RemoveChild vtable call")
    assert parent.address<remove_child.address
    streamdelete=unique(seq_find(dtor,"call","qword ptr [rax]"),"Add task invokes Stream deleting destructor")
    assert remove_child.address<streamdelete.address
    check_delete_flag=[z for z in dtor if z.mnemonic=="mov" and z.op_str=="edx, 1"
                        and 0<streamdelete.address-z.address<20]
    assert len(check_delete_flag)==1
    # Strictly ensure final THIS (RCX) points at the native child object.
    stream_receiver=[z for z in dtor if z.mnemonic=="mov" and z.op_str=="rcx, qword ptr [rbx + 0x40]"
                     and streamdelete.address-28<z.address<streamdelete.address]
    assert len(stream_receiver)==1
    # A task object owns more than a raw Stream: its path destructor too.
    pathdtor=unique([z for z in dtor if is_imp(o,z,"tdb.dll","??1TDB_StreamIDPath@@")],
                     "Add task destructor frees path")
    assert streamdelete.address<pathdtor.address
    reciprocal["add_destructor"]=dict(entry=hex(c["add_dtor"]),owned_flag_offset=hex(f),
        stream_pointer_offset="0x40",owned_flag_check=rva(o,checkflag),
        IsCanonical=rva(o,canonical),GetParent=rva(o,parent),
        parent_RemoveChild_virtual_0x1e0=rva(o,remove_child),
        Stream_deleting_destructor_vtable_0x0=rva(o,streamdelete),
        delete_flag_one=rva(o,check_delete_flag[0]),
        StreamIDPath_destructor=rva(o,pathdtor),
        conditional_rule="owned flag && nonnull && noncanonical; when parent exists, try RemoveChild and assert on failure; delete Stream and task")
    result[ver]=dict(original_BEE_sha256=o["sha"],registered_tasks=receipts,
                     reciprocal_execution_and_Stream_ownership=reciprocal,
                     private_Adobe_runtime_calls=0,foreign_native_Stream_registered=False,
                     caution="Concrete first-party class ownership; not evidence foreign class allowed/safe.")
    print("PASS",ver,"native command table + RTTI + vtables; Add <-> Remove reciprocal task; deleted inverse Add task owns and deletes noncanonical Stream",flush=True)

dst=ROOT/"datasets"/"ae-bee-indexed-add-remove-reciprocal-stream-ownership-2025-2026.json"
dst.write_text(json.dumps({"evidence":"E2-L strict original BEE PE two versions; native RTTI/COL/vtables/IAT/callsite branches; no Adobe code executed",
 "product":"NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM",
 "versions":result},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("SAVED",dst)
