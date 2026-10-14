"""AEIG native document Stream instance pipeline — strict static cross-version verifier.

Examines only installed original Adobe TDB.dll PE images. Does NOT load TDB.dll,
call private functions, attach a child, open/write .aep, or execute After Effects.
Claims are bounded to direct x64 instructions, native RTTI/export/vtable matches.
"""
from pathlib import Path
import subprocess, hashlib, json, re, struct
import pefile, capstone

BIN = {
 "2025": Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll"),
 "2026": Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"),
}
PINNED = {
 "2025":"2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69",
 "2026":"82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b",
}
RE = re.compile(r"^\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)")
CS = capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
CS.detail = True

def load(path,year):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == PINNED[year], f"original installed AE {year} TDB.dll changed: {digest}"
    pe=pefile.PE(str(path))
    base=pe.OPTIONAL_HEADER.ImageBase
    raw=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,
                        errors="replace",check=True).stdout
    sym={int(m.group(1),16):m.group(2) for line in raw.splitlines() if (m:=RE.match(line))}
    iat={im.address-base:(d.dll.decode(errors="replace").lower(),im.name.decode(errors="replace") if im.name else "")
         for d in pe.DIRECTORY_ENTRY_IMPORT for im in d.imports}
    ends={u.struct.BeginAddress:u.struct.EndAddress for u in pe.DIRECTORY_ENTRY_EXCEPTION}
    return {"pe":pe,"base":base,"sym":sym,"iat":iat,"ends":ends,"sha256":digest}

def symbol(p,prefix):
    hits=[a for a,n in p["sym"].items() if n.startswith(prefix)]
    assert len(hits)==1,(prefix,len(hits),[p["sym"][x] for x in hits[:4]])
    return hits[0]

def body(p,a):
    end=p["ends"].get(a)
    assert end is not None and 0 < end-a < 12000,(hex(a),end)
    items=list(CS.disasm(p["pe"].get_data(a,end-a),p["base"]+a))
    assert items and items[0].address-p["base"]==a
    return items

def targets(p,ins):
    out=[]
    for op in ins.operands:
        if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
            out.append(ins.address+ins.size+op.mem.disp-p["base"])
        elif op.type==capstone.x86.X86_OP_IMM and ins.mnemonic in ("call","jmp"):
            out.append(op.imm-p["base"])
    return out

def direct_calls(p,ins,callee):
    return [x for x in ins if x.mnemonic=="call" and callee in targets(p,x)]

def import_calls(p,ins,dll,startswith):
    return [x for x in ins if x.mnemonic=="call" and any(p["iat"].get(a,("",""))[0]==dll
                    and p["iat"][a][1].startswith(startswith) for a in targets(p,x))]

def virtual_calls(ins,offset):
    return [x for x in ins if x.mnemonic=="call" and re.search(
       r"\[(?:rax|rdx|r8|r9|rbx|rdi|rsi)(?: \+ 0x%x)?\]" % offset, x.op_str)
        and f"+ 0x{offset:x}" in x.op_str]

def vtable(p,which):
    return symbol(p,"??_7"+which+"@@6B@")

def slot(p,table,offset):
    t=struct.unpack("<Q",p["pe"].get_data(table+offset,8))[0]-p["base"]
    assert t in p["sym"],(hex(table),hex(offset),hex(t))
    return t

def find_order(p,ins,cname,subname=None):
    cs=[x for x in ins if cname in x.op_str]
    assert cs, (cname,subname)
    return cs

results={}
for year,path in BIN.items():
    p=load(path,year);ex=p["sym"];b=p["base"]
    x={
       "create":symbol(p,"?CreateStream@TDB_StreamFactory@@"),
       "getcanon":symbol(p,"?GetCanonicalStream@TDB_StreamFactory@@"),
       "groupread":symbol(p,"?Read@TDB_StreamGroup@@"),
       "groupwrite":symbol(p,"?Write@TDB_StreamGroup@@"),
       "indexedread":symbol(p,"?ReadAndStore@TDB_IndexedStreamGroup@@"),
       "namedread":symbol(p,"?ReadAndStore@TDB_NamedStreamGroup@@"),
       "indexedappend":symbol(p,"?AppendStream@TDB_IndexedStreamGroup@@"),
       "setparent":symbol(p,"?SetParent@TDB_StreamBase@@"),
       "reverse":symbol(p,"?UpdateReverseIndexVector@TDB_IndexedStreamGroup@@"),
       "reset":symbol(p,"?ResetCachedCapsulePathsFromIndex@TDB_IndexedStreamGroup@@"),
       "setconstant":symbol(p,"?SetConstant@TDB_Stream@@"),
       "always":symbol(p,"?TDB_ShouldAlwaysDecanonicalize@@"),
       "deep":symbol(p,"?TDB_DecanonicalizeAllChildStreamsDeep@@"),
       "matchread":symbol(p,"?Read@TDB_MatchName@@"),
       "endmarker":symbol(p,"?IsEndOfGroupMarker@TDB_MatchName@@"),
       "matchwrite":symbol(p,"?Write@TDB_MatchName@@"),
       "writemarker":symbol(p,"?WriteEndOfGroupMarker@TDB_MatchName@@"),
       "writeid":symbol(p,"?WriteUniqueStreamID@TDB_StreamBase@@"),
    }
    if year=="2025":
        ins= symbol(p,"?InsertStream@TDB_IndexedStreamGroup@@UEAAXIPEAV?$U_ScAutoPtr@VTDB_StreamBase@@@@@Z")
        wrapper=None
    else:
        ins= symbol(p,"?InsertStream@TDB_IndexedStreamGroup@@UEAAXIPEAV?$U_ScAutoPtr@VTDB_StreamBase@@@@AEAUInsertStreamOptions")
        wrapper=symbol(p,"?InsertStream@TDB_IndexedStreamGroup@@UEAAXIPEAV?$U_ScAutoPtr@VTDB_StreamBase@@@@@Z")
    x["indexedinsert"]=ins

    # Validate C++ virtual layout by actual class exports, not guessed slot names.
    vtindex=vtable(p,"TDB_IndexedStreamGroup")
    vtnamed=vtable(p,"TDB_NamedStreamGroup")
    vtleaf=vtable(p,"TDB_Stream")
    assert slot(p,vtindex,0x1b8)==x["indexedread"]
    assert slot(p,vtnamed,0x1b8)==x["namedread"]
    assert slot(p,vtindex,0x1c0)==symbol(p,"?CanStore@TDB_StreamGroup@@")
    if year=="2025":
        assert slot(p,vtindex,0x210)==ins
        assert slot(p,vtindex,0x218)==symbol(p,"?DuplicateStream@TDB_IndexedStreamGroup@@")
    else:
        assert slot(p,vtindex,0x210)==ins and slot(p,vtindex,0x218)==wrapper
        wb=body(p,wrapper)
        assert len(wb)<15 and any(y.mnemonic=="call" and y.op_str=="qword ptr [rax + 0x210]" for y in wb)
    for off,suf in ((0x168,"?GetNumStreams@TDB_IndexedStreamGroup@@"),
                    (0x118,"?Read@TDB_Stream@@")):
        target=slot(p,vtindex if off==0x168 else vtleaf,off)
        assert ex[target].startswith(suf),(hex(off),ex[target])
    assert ex[slot(p,vtleaf,0x80)].startswith("?GetAsLeaf@TDB_Stream@@")
    assert ex[slot(p,vtnamed,0x90)].startswith("?GetAsGroup@TDB_StreamGroup@@")
    assert ex[slot(p,vtleaf,0x190)].startswith("?InsertDefaultKey@TDB_Stream@@")

    # Factory.CreateStream's callback creation occurs outside the registry mutex.
    c=body(p,x["create"])
    locks=import_calls(p,c,"dvacore.dll","?Lock@RecursiveMutex@")
    unlocks=import_calls(p,c,"dvacore.dll","?Unlock@RecursiveMutex@")
    invokes=[y for y in c if y.mnemonic=="call" and y.op_str=="qword ptr [rax + 0x10]"]
    assert len(locks)==1 and len(invokes)==1 and len(unlocks)>=1
    callback=invokes[0]
    preunlock=[y for y in unlocks if y.address<callback.address]
    assert len(preunlock)>=1 and locks[0].address<preunlock[-1].address<callback.address
    # GetAsLeaf, insert default key (initial time 0/1), SetConstant, optional decanonicalization.
    get_leaf=[y for y in c if y.mnemonic=="call" and y.op_str=="qword ptr [rax + 0x80]"]
    insert_key=[y for y in c if y.mnemonic=="call" and
        (y.op_str=="qword ptr [r8 + 0x190]" or (
        year=="2025" and y.op_str=="r8"
        and any(z.op_str.endswith("[rcx + 0x190]") for z in c[max(0,c.index(y)-4):c.index(y)])))]
    assert len(get_leaf)==len(insert_key)==1
    setcon=direct_calls(p,c,x["setconstant"])
    should=direct_calls(p,c,x["always"])
    deep=direct_calls(p,c,x["deep"])
    getgroup=[y for y in c if y.mnemonic=="call" and y.op_str=="qword ptr [rax + 0x90]"]
    assert len(setcon)==len(should)==len(deep)==len(getgroup)==1
    assert callback.address<get_leaf[0].address<insert_key[0].address<setcon[0].address<should[0].address<getgroup[0].address<deep[0].address
    # Deep decanonicalization is gated by a per-call flag and a global predicate.
    assert any(y.mnemonic=="test" and y.op_str=="r12b, r12b" for y in c[c.index(setcon[0]):c.index(should[0])+1])
    assert any(y.mnemonic=="test" and y.op_str=="al, al" for y in c[c.index(should[0]):c.index(getgroup[0])])

    # Native indexed child insertion: type gate, bounds, reorder caches and parent setting.
    ib=body(p,x["indexedinsert"])
    canstore=[y for y in ib if y.mnemonic=="call" and y.op_str=="qword ptr [rax + 0x1c0]"]
    count=[y for y in ib if y.mnemonic=="call" and y.op_str=="qword ptr [rax + 0x168]"]
    rev=direct_calls(p,ib,x["reverse"])
    resets=direct_calls(p,ib,x["reset"])
    parents=direct_calls(p,ib,x["setparent"])
    assert len(canstore)==len(rev)==len(resets)==len(parents)==1 and len(count)>=1, (year, [len(z) for z in (canstore,count,rev,resets,parents)])
    assert canstore[0].address<count[0].address<rev[0].address<parents[0].address
    assert canstore[0].address<resets[0].address<parents[0].address
    assert any(y.mnemonic=="je" and y.address>canstore[0].address
               and y.address<count[0].address for y in ib)
    # Parent pointer state must be committed after row insertion and index update.
    assert any(y.mnemonic=="mov" and y.op_str in ("qword ptr [r13], rbx",
             "qword ptr [r14], rbx", "qword ptr [r12], 0") for y in ib[ib.index(rev[0]):ib.index(parents[0])+1])

    # Real native group loader dispatches by per-child MatchName and virtual group kind.
    rb=body(p,x["groupread"])
    mr=direct_calls(p,rb,x["matchread"]);em=direct_calls(p,rb,x["endmarker"])
    fetch_readhandler=[y for y in rb if y.mnemonic=="mov" and y.op_str=="rbx, qword ptr [rax + 0x1b8]"]
    dispatch=[y for y in rb if y.mnemonic=="call" and y.op_str=="rbx"]
    assert len(mr)==len(em)==len(fetch_readhandler)==len(dispatch)==1
    assert mr[0].address<em[0].address<fetch_readhandler[0].address<dispatch[0].address

    # Indexed ReadAndStore: create by saved MatchName, then group append & virtual Read.
    ird=body(p,x["indexedread"])
    cr=direct_calls(p,ird,x["create"])
    ncount=[y for y in ird if y.mnemonic=="call" and y.op_str=="qword ptr [rdx + 0x168]"]
    if year=="2025":
        app_load=[y for y in ird if y.mnemonic=="mov" and y.op_str=="r9, qword ptr [rcx + 0x210]"]
        append=[y for y in ird if y.mnemonic=="call" and y.op_str=="r9" and
                app_load and y.address>app_load[0].address]
        read_load=[y for y in ird if y.mnemonic=="mov" and y.op_str=="rbx, qword ptr [rax + 0x118]"]
        do_read=[y for y in ird if y.mnemonic=="call" and y.op_str=="rbx" and
                 read_load and y.address>read_load[0].address]
        assert len(app_load)==len(read_load)==1
    else:
        append=[y for y in ird if y.mnemonic=="call" and y.op_str=="qword ptr [r9 + 0x218]"]
        do_read=[y for y in ird if y.mnemonic=="call" and y.op_str=="qword ptr [rbx + 0x118]"]
    assert len(cr)==len(ncount)==len(append)==len(do_read)==1
    assert cr[0].address<ncount[0].address<append[0].address<do_read[0].address
    assert any(z.mnemonic=="test" and z.op_str=="rax, rax" and
               cr[0].address<z.address<ncount[0].address for z in ird)

    # Named Load path also uses CreateStream and has typed editor/upgrade behavior.
    nrd=body(p,x["namedread"])
    ncreate=direct_calls(p,nrd,x["create"])
    upgrade=[y for y in nrd if y.mnemonic=="call" and y.op_str=="qword ptr [rax + 0x1b0]"]
    if year=="2025":
        nreads=[y for y in nrd if y.mnemonic=="call" and y.op_str=="rdi"]
        assert len(nreads)==2 and len([y for y in nrd if y.mnemonic=="mov" and y.op_str=="rdi, qword ptr [rax + 0x118]"])==2
    else:
        nreads=[y for y in nrd if y.mnemonic=="call" and y.op_str=="qword ptr [rdi + 0x118]"]
    assert len(ncreate)==len(upgrade)==1 and nreads
    assert ncreate[0].address<upgrade[0].address
    # Native StreamGroup write emits IDs, uses canonical MatchName, and end-marker.
    wb=body(p,x["groupwrite"])
    assert len(direct_calls(p,wb,x["writeid"]))==1
    assert len(direct_calls(p,wb,x["getcanon"]))>=1
    assert len(direct_calls(p,wb,x["matchwrite"]))==1
    assert len(direct_calls(p,wb,x["writemarker"]))==1

    row={
      "sha256":p["sha256"],
      "CreateStream":{
        "function_rva":hex(x["create"]),
        "mutex_lock":hex(locks[0].address-b),
        "success_mutex_unlock_before_creator":hex(preunlock[-1].address-b),
        "std_function_creator_invocation":hex(callback.address-b),
        "GetAsLeaf":hex(get_leaf[0].address-b),
        "InsertDefaultKey":hex(insert_key[0].address-b),
        "SetConstant":hex(setcon[0].address-b),
        "ShouldAlwaysDecanonicalize":hex(should[0].address-b),
        "GetAsGroup":hex(getgroup[0].address-b),
        "DecanonicalizeAllChildStreamsDeep":hex(deep[0].address-b),
        "note":"Default key, constant, and deep decanonicalization are conditional; not every Stream invokes them."
      },
      "IndexedInsert":{
        "function_rva":hex(x["indexedinsert"]),
        "simple_wrapper_rva":hex(wrapper) if wrapper else None,
        "CanStore_virtual_0x1c0":hex(canstore[0].address-b),
        "GetNumStreams_virtual_0x168":hex(count[0].address-b),
        "reverse_index_update":hex(rev[0].address-b),
        "path_cache_reset":hex(resets[0].address-b),
        "SetParent":hex(parents[0].address-b),
        "vtable_InsertStream_entry_offset":hex(0x210 if year=="2025" else 0x218),
        "options_overload_present":year=="2026"
      },
      "GroupRead":{
        "function_rva":hex(x["groupread"]),
        "Read_MatchName":hex(mr[0].address-b),
        "IsEndOfGroupMarker":hex(em[0].address-b),
        "ReadAndStore_vtable_offset":"0x1b8",
        "ReadAndStore_dispatch":hex(dispatch[0].address-b),
        "ReadAndStore_Indexed":hex(x["indexedread"]),
        "ReadAndStore_Named":hex(x["namedread"]),
        "Indexed_CreateStream":hex(cr[0].address-b),
        "Indexed_GetNumStreams":hex(ncount[0].address-b),
        "Indexed_InsertStream":hex(append[0].address-b),
        "Indexed_Read_child":hex(do_read[0].address-b),
        "Named_CreateStream":hex(ncreate[0].address-b),
        "Named_UpgradeChildStream":hex(upgrade[0].address-b),
        "Native_Group_WriteUniqueStreamID":hex(direct_calls(p,wb,x["writeid"])[0].address-b),
        "Native_Group_CanonicalLookup_Write_count":len(direct_calls(p,wb,x["getcanon"])),
        "Native_Group_WriteMatchName":hex(direct_calls(p,wb,x["matchwrite"])[0].address-b),
        "Native_Group_WriteEndMarker":hex(direct_calls(p,wb,x["writemarker"])[0].address-b),
      },
      "limitations":["No in-host project read/write executed",
                     "No proof of malformed/missing creator recovery",
                     "Raw vtable ABI private, version-specific",
                     "No evidence foreign CNL type can be registered"]
    }
    results[year]=row
    print("PASS",year,"Creator unlock-before-callback, time defaults, canonicalization,",
          "index CanStore/parent, archive MatchName-to-Creator-to-Insert-to-Read")
    print("  Create",row["CreateStream"])
    print("  Insert",row["IndexedInsert"])
    print("  Load",row["GroupRead"])

OUT = Path(__file__).resolve().parents[4] / "datasets" / "ae-tdb-document-instance-create-insert-load-2025-2026.json"
OUT.parent.mkdir(exist_ok=True, parents=True)
OUT.write_text(json.dumps({"evidence":"E2-L read-only original installed PE; static success-branch tracing",
   "product_gate":"NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM",
   "versions":results},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PASS all, receipts",OUT)
