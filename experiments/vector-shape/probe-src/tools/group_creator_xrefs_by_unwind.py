"""True x64 runtime-function boundaries for host Vector stream creator RIP references.
Windows .pdata unwind table, not the nearest exported-symbol heuristic.
"""
import pefile,json,bisect,collections
from pathlib import Path
o=json.load(open(r"D:\Developer\After Effects Internals Guide\datasets\ae-vector-stream-creators-static-xrefs-2025-2026.json"))
for ver,p in (("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")):
    pe=pefile.PE(p)
    funcs=[(r.struct.BeginAddress,r.struct.EndAddress) for r in pe.DIRECTORY_ENTRY_EXCEPTION]
    funcs.sort()
    starts=[x[0] for x in funcs]
    grouped=collections.defaultdict(list)
    misses=[]
    for entry in o["versions"][ver]["functions"]:
        for ref in entry["static_refs"]:
            address=int(ref["source_rva"],16)
            i=bisect.bisect_right(starts,address)-1
            if i>=0 and address<funcs[i][1]:
                key=(hex(funcs[i][0]),hex(funcs[i][1]))
                grouped[key].append((entry["export"],ref["source_rva"]))
            else:misses.append((entry["export"],hex(address)))
    print("==",ver,"pdata functions",len(funcs),"groups",len(grouped),"missed",len(misses))
    for key,refs in sorted(grouped.items()):
        print("FUNCTION",key,"size",int(key[1],16)-int(key[0],16),"refs",len(refs))
        for name,at in refs[:45]:
            print(" ",at,name.split("@")[1][:85] if "@" in name else name[:85])
