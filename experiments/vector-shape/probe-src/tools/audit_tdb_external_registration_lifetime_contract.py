"""EXP-SHAPE-024: Read-only TDB external-registration ABI feasibility audit.

Records compact facts from disassembled, exact BEE 2025/2026 TDB.dll
exported functions, including std::function virtual target lifecycle, factory
startup, eager canonical construction and unregister order.

NO Adobe function is invoked and NO Adobe binary or proprietary assembly dump
is distributed by this verifier.
"""
from pathlib import Path
from bisect import bisect_right
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
import subprocess, pefile, re, json, hashlib
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
BINARIES={
"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll")
}
SELECTORS={
"registry_register":"?RegisterFactoryFunc@TDB_StreamFactory@@",
"registry_unregister":"?UnregisterFactoryFunc_NullOK@TDB_StreamFactory@@",
"stream_create":"?CreateStream@TDB_StreamFactory@@",
"registration_wrapper":"?Register@TDB_ScRegisterStreams@@",
"unregister_all":"?UnregisterAll@TDB_ScRegisterStreams@@",
"registration_wrapper_destructor":"??1TDB_ScRegisterStreams@@",
"registry_destructor":"??1TDB_StreamFactory@@",
"canonical_register":"?RegisterCanonicalInstance@TDB_StreamFactory@@"
}
REGEX=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
results={}
for ver,path in BINARIES.items():
    data=path.read_bytes();pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
    syms={}
    p=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,
                     text=True,errors="replace",check=True)
    for line in p.stdout.splitlines():
        m=REGEX.match(line)
        if m:syms[int(m.group(1),16)]=m.group(2)
    pdata=sorted((i.struct.BeginAddress,i.struct.EndAddress)
                 for i in pe.DIRECTORY_ENTRY_EXCEPTION)
    starts=[r[0] for r in pdata]
    d=Cs(CS_ARCH_X86,CS_MODE_64);d.detail=True
    functions={}
    for key,query in SELECTORS.items():
        hits=[(rva,name) for rva,name in syms.items() if name.startswith(query)]
        assert len(hits)==1,(ver,key,len(hits))
        rva,name=hits[0]
        j=bisect_right(starts,rva)-1
        assert j>=0 and pdata[j][0]<=rva<pdata[j][1],(ver,key,rva)
        end=pdata[j][1]
        assert end-rva<3000,(ver,key,end-rva)
        code=data[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(end)]
        ops=[]
        for ins in d.disasm(code,base+rva):
            target=None
            if ins.operands and ins.mnemonic in ("call","jmp"):
                op=ins.operands[0]
                if op.type==X86_OP_IMM:target=op.imm
                elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                    target=ins.address+ins.size+op.mem.disp
            ops.append({"rva":hex(ins.address-base),"opcode":ins.mnemonic,
                        "operands":ins.op_str,
                        "target":syms.get(target-base,"") if target else ""})
        functions[key]={"rva":hex(rva),"symbol":name,"instructions":ops}
    def pick(key, *, opcode=None, operand=None, symbol=None):
        ops=functions[key]["instructions"]
        return [o for o in ops if (opcode is None or o["opcode"]==opcode)
                and (operand is None or operand in o["operands"])
                and (symbol is None or symbol in o["target"])]
    def exactly(key, **kwargs):
        x=pick(key,**kwargs)
        assert x,(ver,key,kwargs)
        return [i["rva"] for i in x]
    # Callback lifecycle: TDB factory owns/copies std::function-erased objects.
    fn_copy=exactly("registry_register",opcode="call",operand="qword ptr [rax]")
    fn_delete=exactly("registry_register",opcode="call",operand="qword ptr [rax + 0x20]")
    fn_invoke=exactly("stream_create",opcode="call",operand="qword ptr [rax + 0x10]")
    # Registration MUST clone a new stream before it returns.
    create_call=exactly("registry_register",opcode="call",symbol="?CreateStream@TDB_StreamFactory@@")
    canonical_checks={x:exactly("registry_register",opcode="call",operand=f"[rax + 0x{x}]")
                      for x in ("58","80","150")}
    separated=exactly("registry_register",opcode="call",symbol="?RegisterSeparatedDimensions@TDB_StreamFactory@@")
    # Register has a copied std::function (register wrapper forwards),
    # a Bool result condition, and a copied MatchName in owned vector list.
    wrap_reg=exactly("registration_wrapper",opcode="call",symbol="?RegisterFactoryFunc@TDB_StreamFactory@@")
    vector_advance=exactly("registration_wrapper",opcode="add",operand="qword ptr [rbx + 8], 0x10")
    unregister_invocations=exactly("unregister_all",opcode="call",
                                   symbol="?UnregisterFactoryFunc@TDB_StreamFactory@@")
    backward=exactly("unregister_all",opcode="add",operand="rbx, -0x10")
    # Critical counterexample to an RAII assumption: ScRegisterStreams::~ only
    # frees a vector, does not call UnregisterAll; explicit call is required.
    sc_destructor_calls=[x["target"] for x in pick("registration_wrapper_destructor",
                              opcode="call") if x["target"]]
    assert not any("UnregisterAll" in c for c in sc_destructor_calls),(ver,sc_destructor_calls)
    # Unregister removes the original factory and canonical maps before it
    # releases an object, and the release is a native virtual call.
    destroy_native=exactly("registry_unregister",opcode="call",operand="qword ptr [rax]")
    explicit_destructor_argument=exactly("registry_unregister",opcode="mov",operand="edx, 1")
    mutex_unlock=exactly("registry_unregister",opcode="call",
                         operand="qword ptr [rip +")
    # Distinguish generic TDB factory's own bulk teardown from helper wrapper dtor.
    factory_dtor_locks=exactly("registry_destructor",opcode="call",operand="qword ptr [rip +")
    results[ver]={
      "binary_sha256":hashlib.sha256(data).hexdigest(),
      "factory_register_rva":functions["registry_register"]["rva"],
      "factory_create_rva":functions["stream_create"]["rva"],
      "factory_unregister_inner_rva":functions["registry_unregister"]["rva"],
      "factory_destructor_rva":functions["registry_destructor"]["rva"],
      "sc_wrapper_destructor_rva":functions["registration_wrapper_destructor"]["rva"],
      "register_wrapper_rva":functions["registration_wrapper"]["rva"],
      "unregister_all_rva":functions["unregister_all"]["rva"],
      "register_factory_clones_std_function_via_virt_slot0":fn_copy,
      "register_factory_destroys_temporary_std_function_via_virt_slot_0x20":fn_delete,
      "create_stream_invokes_std_function_via_virt_slot_0x10":fn_invoke,
      "registration_eager_CreateStream_sites":create_call,
      "register_streams_wrapper_invoke_factory":wrap_reg,
      "registration_wrapper_record_advance":vector_advance,
      "eager_stream_virtual_post_create_checks":canonical_checks,
      "canonical_separated_dimension_registration_sites":separated,
      "explicit_unregister_all_reverse_iteration":backward,
      "unregister_all_unlinks_names":unregister_invocations,
      "sc_registration_wrapper_destructor_calls_unregister_all":False,
      "factory_unregister_native_destructor_virtual_call":destroy_native,
      "factory_unregister_native_destructor_argument_1":explicit_destructor_argument,
      "factory_destructor_has_independent_cleanup":bool(factory_dtor_locks),
      "third_party_abi_safe":False,
      "private_registration_executed":False,
    }
    print("PASS",ver,"factory copies callback and eagerly creates stream;",
          "UnregisterAll explicitly walks registered keys backward;",
          "registration wrapper destructor does not call UnregisterAll",
          flush=True)
dest=ROOT/"datasets"/"ae-native-stream-private-registration-lifetime-2025-2026.json"
dest.write_text(json.dumps({
"classification":"E2-L native machine-code facts; not host plugin compatibility",
"method":"compare unique exported function addresses and .pdata-bounded instructions against targeted concrete native calls",
"result":"cross-version checks passed; external TDB type registration not performed",
"warnings":["register factory eagerly constructs native stream, expects correct vtable and allocator",
"std::function-erased callback may outlive plugin; explicit unregister required",
"factory separate canonical/map lifetime and host shutdown timing not established",
"experimental version-pinned complete ABI required before attempting registration"],
"versions":results
},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SAVED",dest,flush=True)
