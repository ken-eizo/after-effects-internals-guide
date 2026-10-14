"""F-VECTOR-100 — Strict static native TDB archive error-policy probe.
Original pinned AE2025/2026 TDB.dll only; no mutation, no host execution.
Checks loader's CreateStream fifth argument and missing-creator error route.
"""
from pathlib import Path
import pefile,subprocess,capstone,re,hashlib,json
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
FILES={
"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"}
EXPECTED={
"2025":"2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69",
"2026":"82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b"}
rx=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)")
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
def collect(year):
    p=Path(FILES[year]);d=p.read_bytes()
    digest=hashlib.sha256(d).hexdigest();assert digest==EXPECTED[year]
    pe=pefile.PE(data=d);base=pe.OPTIONAL_HEADER.ImageBase
    rows=subprocess.run(["dumpbin","/exports",str(p)],capture_output=True,text=True,check=True,
                        errors="replace").stdout.splitlines()
    exp={int(z.group(1),16):z.group(2) for l in rows if (z:=rx.match(l))}
    iat={j.address-base:(e.dll.decode(errors="replace").lower(),
                         j.name.decode(errors="replace") if j.name else "")
         for e in pe.DIRECTORY_ENTRY_IMPORT for j in e.imports}
    pdata={q.struct.BeginAddress:q.struct.EndAddress for q in pe.DIRECTORY_ENTRY_EXCEPTION}
    def lookup(prefix):
        out=[a for a,n in exp.items() if n.startswith(prefix)]
        assert len(out)==1,(prefix,out)
        return out[0]
    def body(a):
        end=pdata[a]
        assert 0<end-a<4000
        return list(cs.disasm(pe.get_data(a,end-a),base+a))
    def tgt(i):
        if not i.operands:return None
        x=i.operands[0]
        if x.type==X86_OP_IMM:return x.imm-base
        if x.type==X86_OP_MEM and x.mem.base==X86_REG_RIP:return i.address+i.size+x.mem.disp-base
    create=lookup("?CreateStream@TDB_StreamFactory@@")
    cb=body(create)
    errflag=[z for z in cb if z.mnemonic=="cmp" and z.op_str=="byte ptr [rbp + 0x130], 0"]
    assert len(errflag)==1,(year,errflag)
    flag=errflag[0]
    # The next branch skips error handling when false.
    nextops=[z for z in cb if flag.address<z.address<flag.address+30]
    je=[z for z in nextops if z.mnemonic=="je" and z.operands[0].type==X86_OP_IMM]
    assert je and je[0].address-flag.address<14
    branch_target=tgt(je[0])
    missing_reports=[z for z in cb if z.mnemonic=="call"
                     and (pval:=tgt(z)) in iat
                     and iat[pval][0]=="u.dll"
                     and iat[pval][1].startswith("Up_ReportCoSAErrString")]
    # At least one error report executes in the branch-not-taken region,
    # i.e., between the flag check and the flag-false destination.
    direct_report=[z for z in missing_reports
                   if flag.address<z.address<base+branch_target]
    assert len(direct_report)==1,(year,[hex(z.address-base) for z in missing_reports])
    cond_null=[z for z in cb if z.mnemonic=="cmp" and z.op_str=="byte ptr [rbp + 0x130], al"]
    assert len(cond_null)==1,("Creator null return flag check",year)

    def read_policy(group):
        a=lookup(f"?ReadAndStore@TDB_{group}StreamGroup@@")
        ops=body(a)
        ctor=[z for z in ops if z.mnemonic=="call" and tgt(z)==create]
        assert len(ctor)==1,("loader invokes factory",group)
        prefix=[z for z in ops if z.address<ctor[0].address]
        expected_report_flag = 1 if group=="Indexed" else 0
        set5=[z for z in prefix if z.mnemonic=="mov" and z.op_str==f"byte ptr [rsp + 0x20], {expected_report_flag}"]
        set6=[z for z in prefix if z.mnemonic=="mov" and z.op_str=="byte ptr [rsp + 0x28], 0"]
        assert len(set5)==len(set6)==1,(year,group,expected_report_flag)
        # Native Win64 ABI: caller stack+0x20 at CALL -> callee entry+0x28.
        # CreateStream saves rbp at function-entry rsp -0x108 and tests
        # [rbp+0x130] == callee entry rsp +0x28, the fifth argument.
        assert cb[0].op_str=="qword ptr [rsp + 0x18], rbx"
        assert any(z.mnemonic=="lea" and z.op_str=="rbp, [rsp - 0xd0]" for z in cb[:22])
        assert sum(z.mnemonic=="push" for z in cb[:22])==7
        return dict(entry=hex(a),missing_creator_error_report_flag=expected_report_flag,
                    set_error_flag_callsite=hex(set5[0].address-base),
                    pass_next_stack_flag_0=hex(set6[0].address-base),
                    create_call=hex(ctor[0].address-base),
                    rationale="Win64 stack argument #5: caller rsp+0x20 -> callee entry+0x28 = rbp+0x130")
    named=read_policy("Named")
    indexed=read_policy("Indexed")
    row=dict(original_TDB_sha256=digest,create_entry=hex(create),
             missing_Creator_first_stack_flag_check=hex(flag.address-base),
             missing_Creator_skip_report_if_false=hex(je[0].address-base),
             missing_Creator_Adobe_error_report_call=hex(direct_report[0].address-base),
             returned_null_Creator_first_stack_flag_check=hex(cond_null[0].address-base),
             loader_named=named,loader_indexed=indexed,
             proven="Indexed archive loader enables and Named loader disables the missing-Creator Adobe error-report policy flag before calling CreateStream; behavior after U.dll error report is unverified.",
             not_proven="U.dll report behavior, exception/dialog, .aep recovery, preservation, foreign CNL roundtrip.")
    print("PASS",year,"Indexed missing-Creator report flag=1; Named flag=0; static U.dll report branch",flush=True)
    return row
result={v:collect(v) for v in ("2025","2026")}
dest=ROOT/"datasets"/"ae-tdb-archive-unregistered-creator-report-gate-2025-2026.json"
dest.write_text(json.dumps({"evidence":"E2-L deterministic SHA-pinned original installed native machine code; no Adobe function called",
                            "versions":result},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("SAVED",dest)
