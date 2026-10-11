import subprocess,re
for version,path in [("2025",r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll"),("2026",r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll")]:
    s=subprocess.run(["dumpbin","/exports",path],capture_output=True,text=True,errors="replace").stdout
    lines=s.splitlines()
    term_map={
      "factory_owner":["@TDB_StreamFactory@@","TDB_StreamFactory@@","@TDB_StreamBase@@"],
      "registration":["Register","InsertFactory","AddFactory","Registry","RegisterStream"],
      "vector_layer_creation":["BEE_VectorLayer","BEE_VectorArt"],
      "tool_editing":["VectorPathTool","VectorEdit","ShapeTool","PenTool","ToolSuite","PathEdit"],
    }
    print("===",version)
    for key,needles in term_map.items():
        hits=[line for line in lines if any(token in line for token in needles)]
        print(key,len(hits))
        for v in hits[:24]:print(" ",v.strip()[:200])
