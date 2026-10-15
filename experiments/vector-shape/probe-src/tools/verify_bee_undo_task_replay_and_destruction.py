"""EXP-SHAPE-101: Native BEE Undo/Redo task replay, two-stack cleanup and task destruction.

Original SHA-pinned installed After Effects 2025 and 2026 BEE.dll files only.
Never loads Adobe code, attaches to an AE process, changes a user project,
or invokes private APIs. Checks machine instructions, call order, native
imports and cross-function links. This does not prove StreamBase ownership.
"""
from pathlib import Path
import hashlib,json,subprocess,re,pefile,capstone
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
FILES={
 "2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
SHA={
 "2025":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730",
 "2026":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e"}
RX=re.compile(r"^\s*\d+\s+[A-Fa-f0-9]+\s+([A-Fa-f0-9]{8})\s+(\S+)")
CS=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);CS.detail=True
def openpe(year):
    f=Path(FILES[year]);d=f.read_bytes();h=hashlib.sha256(d).hexdigest()
    assert h==SHA[year],("Unexpected original Adobe BEE.dll binary",year,h)
    p=pefile.PE(data=d);base=p.OPTIONAL_HEADER.ImageBase
    raw=subprocess.run(["dumpbin","/exports",str(f)],capture_output=True,
                        text=True,errors="replace",check=True).stdout.splitlines()
    syms={int(m.group(1),16):m.group(2) for line in raw if (m:=RX.match(line))}
    imports={entry.address-base:(dll.dll.decode(errors="replace").lower(),
                                entry.name.decode(errors="replace") if entry.name else "")
             for dll in p.DIRECTORY_ENTRY_IMPORT for entry in dll.imports}
    ends={z.struct.BeginAddress:z.struct.EndAddress for z in p.DIRECTORY_ENTRY_EXCEPTION}
    return dict(pe=p,base=base,syms=syms,imports=imports,ends=ends,sha=h)
def exp(o,prefix):
    matches=[(r,s) for r,s in o["syms"].items() if s.startswith(prefix)]
    assert len(matches)==1,(prefix,len(matches))
    return matches[0][0]
def block(o,a):
    end=o["ends"].get(a)
    assert end and 0<end-a<25000,(hex(a),end)
    v=list(CS.disasm(o["pe"].get_data(a,end-a),o["base"]+a))
    assert v and v[0].address==o["base"]+a
    return v
def target(o,i):
    if not i.operands:return None
    a=i.operands[0]
    if i.mnemonic in ("jmp","call") and a.type==X86_OP_IMM:return a.imm-o["base"]
    if i.mnemonic in ("jmp","call") and a.type==X86_OP_MEM and a.mem.base==X86_REG_RIP:
        return i.address+i.size+a.mem.disp-o["base"]
    return None
def calls(o,b,t):
    return [i for i in b if i.mnemonic=="call" and target(o,i)==t]
def imports(o,b,dll,prefix):
    return [i for i in b if i.mnemonic=="call" and (t:=target(o,i)) is not None
            and o["imports"].get(t,("",""))[0]==dll
            and o["imports"][t][1].startswith(prefix)]
def matches(b,mnemonic,operands):
    return [i for i in b if i.mnemonic==mnemonic and i.op_str==operands]
def one(v,why):
    assert len(v)==1,(why,len(v),[hex(x.address) for x in v[:8]])
    return v[0]
def at(o,i):return hex(i.address-o["base"])

result={}
for year in FILES:
    o=openpe(year)
    dtor=exp(o,"??1BEE_UndoContext@@")
    clearstack=exp(o,"?ClearStack@BEE_UndoContext@@")
    clearundo=exp(o,"?ClearUndoStack@BEE_UndoContext@@")
    clearredo=exp(o,"?ClearRedoStack@BEE_UndoContext@@")
    undo=exp(o,"?BEE_Undo@@YAHAEAVBEE_UndoContext@@")
    redo=exp(o,"?BEE_Redo@@YAHAEAVBEE_UndoContext@@")
    undobody=block(o,undo);redobody=block(o,redo)
    ctxbody=block(o,dtor)
    clearbody=block(o,clearstack)
    undoclear=block(o,clearundo);redoclear=block(o,clearredo)

    # Locate a shared native TaskStack cleanup helper via 3 exact callsites.
    uc=[z for z in undoclear if z.mnemonic=="call" and target(o,z) is not None]
    rc=[z for z in redoclear if z.mnemonic=="call" and target(o,z) is not None]
    wc=[z for z in clearbody if z.mnemonic=="call" and target(o,z) is not None]
    assert len(uc)==len(rc)==len(wc)==1
    helper=target(o,uc[0]);assert helper==target(o,rc[0])==target(o,wc[0])
    assert len(calls(o,ctxbody,helper))==2,("UndoContext destructor must clear both TaskStacks",year)
    # The second destructor cleanup must be on the other stack embedded at +0x28.
    dtor_undo,dtor_redo=calls(o,ctxbody,helper)
    assert dtor_undo.address<dtor_redo.address
    head=[z for z in ctxbody if dtor_undo.address<z.address<dtor_redo.address]
    assert matches(head,"lea","rdx, [rdi + 0x28]"),"Second stack offset +0x28"
    assert matches(undoclear,"mov","rdx, rcx") or matches(undoclear,"mov","rdx, rbx")
    assert matches(redoclear,"lea","rbx, [rcx + 0x28]") or matches(redoclear,"lea","rdx, [rcx + 0x28]")

    b=block(o,helper)
    getitem=one(imports(o,b,"list.dll","LIST_GetItem"),"list item read")
    removelist=one(imports(o,b,"list.dll","LIST_RemoveRange"),"list range removal")
    deleting=one(matches(b,"call","qword ptr [rax]"),"task object deleting virtual dispatch")
    assert getitem.address<deleting.address<removelist.address
    delete_flag_sources=[z for z in b if z.mnemonic=="mov" and
                         z.op_str in ("edx, 1","edx, ebx") and
                         0<deleting.address-z.address<20]
    assert len(delete_flag_sources)==1
    if delete_flag_sources[0].op_str=="edx, ebx":
        # 2026 loads one into EBX and then forwards it as the scalar-delete flag.
        assert matches(b,"mov","ebx, 1")
        assert delete_flag_sources[0].address<deleting.address
    # Both original binaries pass the task-owned native pointer at [rsp+0x40]
    # to the vtable[0] deleting destructor.
    assert len([z for z in b if z.mnemonic=="mov" and z.op_str=="rcx, qword ptr [rsp + 0x40]"
                and 0<deleting.address-z.address<30])==1

    # Undo/Redo each remove a history record, call the same replay engine
    # and pass its returned record to a native history-stack insertion helper.
    uremove=one(imports(o,undobody,"list.dll","LIST_Remove"),"Undo removes a record")
    rremove=one(imports(o,redobody,"list.dll","LIST_Remove"),"Redo removes a record")
    candidates={target(o,z) for z in undobody if z.mnemonic=="call" and target(o,z) is not None}
    candidates &= {target(o,z) for z in redobody if z.mnemonic=="call" and target(o,z) is not None}
    recandidates=[]
    for addr in candidates:
        if addr is None or addr not in o["ends"]:continue
        z=block(o,addr)
        if matches(z,"mov","qword ptr [r12 + 0x20], rax") or matches(z,"mov","qword ptr [rbx + 0x20], rax"):
            recandidates.append(addr)
    replay=one(recandidates,"common inverse command task record executor")
    urep=one(calls(o,undobody,replay),"Undo invoke task")
    rrep=one(calls(o,redobody,replay),"Redo invoke task")
    assert uremove.address<urep.address and rremove.address<rrep.address
    replaybody=block(o,replay)
    recinput=one([z for z in replaybody if z.mnemonic=="mov" and z.op_str in
                  ("rcx, qword ptr [r12 + 0x20]","rcx, qword ptr [r15 + 0x20]")],
                 "task input pointer at record +0x20")
    # Ignore profiler calls; find the +8 callback after the input record load.
    executed=one([z for z in replaybody if z.mnemonic=="call" and
                  z.op_str=="qword ptr [rax + 8]" and 0<z.address-recinput.address<30],
                 "replay task vtable+8")
    inverse=one([z for z in replaybody if z.mnemonic=="mov" and z.op_str in
                 ("qword ptr [rbx + 0x20], rax","qword ptr [r12 + 0x20], rax")
                 and 0<z.address-executed.address<24],
                "callback returns next history task")
    assert recinput.address<executed.address<inverse.address
    # Identify common stack requeue function from calls after the replay, and
    # require a direct call to it from both Undo and Redo.
    requeue_candidates=[]
    for t in candidates:
        if t not in o["ends"] or t==replay:continue
        us=[z for z in calls(o,undobody,t) if z.address>urep.address]
        rs=[z for z in calls(o,redobody,t) if z.address>rrep.address]
        if us and rs:
            # A stack-store function is passed a record pointer via lea rcx, [rsp].
            uix=undobody.index(us[0]);rix=redobody.index(rs[0])
            up=undobody[max(0,uix-4):uix]
            rp=redobody[max(0,rix-4):rix]
            if any(z.mnemonic=="lea" and z.op_str.startswith("rcx, [rsp") for z in up) and any(
                  z.mnemonic=="lea" and z.op_str.startswith("rcx, [rsp") for z in rp):
                requeue_candidates.append(t)
    requeue=one(requeue_candidates,"same history record append procedure from both Undo/Redo")

    row={
      "original_BEE_sha256":o["sha"],
      "UndoContext_destructor":{
        "entry":hex(dtor),
        "first_undo_stack_cleanup":at(o,dtor_undo),
        "second_redo_stack_cleanup":at(o,dtor_redo),
        "redo_stack_embedded_offset":"0x28",
      },
      "history_clear":{
        "shared_helper":hex(helper),
        "ClearStack_wrapper":hex(clearstack),
        "ClearUndoStack_call":at(o,uc[0]),
        "ClearRedoStack_call":at(o,rc[0]),
        "LIST_GetItem":at(o,getitem),
        "virtual_deleting_destructor_vtable_0x0":at(o,deleting),
        "delete_flag":"edx=1",
        "LIST_RemoveRange":at(o,removelist),
        "record_task_pointer_offset":"0x20",
      },
      "undo_redo":{
        "BEE_Undo":hex(undo),"BEE_Redo":hex(redo),
        "undo_LIST_Remove":at(o,uremove),
        "redo_LIST_Remove":at(o,rremove),
        "shared_task_replay_helper":hex(replay),
        "undo_calls_task_replay":at(o,urep),
        "redo_calls_task_replay":at(o,rrep),
        "task_input_from_record_0x20":at(o,recinput),
        "task_execute_virtual_offset_0x8":at(o,executed),
        "task_return_pointer_into_output_record_0x20":at(o,inverse),
        "shared_requeue_helper":hex(requeue),
      },
      "scope":"E2-L original native x64 disassembly only; no host executed, no third-party type",
      "unresolved":["Concrete task class for Indexed Stream remove/add/reorder",
                    "How exactly task owns detached TDB_StreamBase or clones",
                    "Exception paths in Undo/Redo and project close"]}
    result[year]=row
    print("PASS",year,"UndoContext cleanup both TaskStacks; per-task deleting dtor; Undo/Redo shared replay via +8 returns reciprocal history task; requeues",flush=True)
    print(" UndoContext",hex(dtor),"cleanup",hex(helper),"replay",hex(replay),"requeue",hex(requeue),flush=True)

path=ROOT/"datasets"/"ae-bee-undo-task-reciprocal-replay-destruction-2025-2026.json"
path.write_text(json.dumps({"status":"PASS strict static both installed AE versions",
 "external_native_class_registered":False,"private_functions_invoked":False,
 "versions":result},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("SAVED",path)
