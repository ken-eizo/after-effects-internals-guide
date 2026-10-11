import json
x=json.load(open(r"D:\Developer\After Effects Internals Guide\datasets\ae-tdb-register-callsite-disasm-2025-2026.json"))
for dll,item in x["versions"]["2026"].items():
    for f in item["samples"]:
        if any(w in f["name"] for w in ("Get_AE_StreamFactory@@","Register@TDB_ScRegisterStreams@@","RegisterStreams@BEE_Layer@@","RegisterFactoryFunc@TDB_StreamFactory@@")):
            print("\n==",dll,f["name"],"==")
            for k in f["instructions"][:220]:
                print(k["rva"],k["op"],k["operands"],("-> "+k["callee"][:110]) if k["callee"] else "")
