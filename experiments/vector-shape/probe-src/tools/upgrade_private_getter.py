"""Add opt-in, read-only private TDB getter probe to ShapeLayerAE.
No call until user chooses the explicitly named Animation menu command.
NEVER dereference/modify the private factory pointer.
"""
from pathlib import Path
p=Path(r"D:\Developer\ShapeLayerAE\src\ShapeLayerProbe.cpp")
s=p.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1,(old[:100],s.count(old))
    s=s.replace(old,new,1)
sub("#include <string>", "#include <string>\n#if defined(MSWindows)\n#include <Windows.h>\n#endif")
sub("static AEGP_Command g_unknown_command = 0;", "static AEGP_Command g_unknown_command = 0;\nstatic AEGP_Command g_private_command = 0;")
before="static A_Err CommandHook(AEGP_GlobalRefcon, AEGP_CommandRefcon,"
private=r'''// EXPLICIT OPT-IN ONLY: read-only invocation of private *getter*, pinned by its
// trivial x64 instruction fingerprint. No factory object dereference, registration,
// typed callback, memory patching, or private vector creation.
static A_Err ProbePrivateTDBFactoryGetter() {
    if (!g_basic) return A_Err_NONE;
    AEGP_SuiteHandler s(g_basic);
    const char* tmp = getenv("TEMP");
    const std::string path = std::string(tmp ? tmp : ".") +
                             "\\ShapeLayerAE_private_factory_probe.tsv";
    FILE* output = fopen(path.c_str(), "wb");
    if (!output) {
        s.UtilitySuite3()->AEGP_ReportInfo(g_id,
                 "ShapeLayerAE: Cannot write private probe log.");
        return A_Err_NONE;
    }
    int module_found=0, export_found=0, fingerprint_ok=0, result_nonnull=0;
#if defined(MSWindows) && defined(_M_X64)
    HMODULE tdb = GetModuleHandleW(L"TDB.dll");
    if (tdb) {
        module_found=1;
        FARPROC getter=GetProcAddress(
             tdb, "?Get_AE_StreamFactory@@YAPEAVTDB_StreamFactory@@XZ");
        if (getter) {
            export_found=1;
            const unsigned char* b =
                reinterpret_cast<const unsigned char*>(getter);
            // AE 2025/26 exact exports are mov rax, [rip+disp32]; ret.
            // Reject any other code shape BEFORE attempting even a read-only call.
            if (b[0]==0x48 && b[1]==0x8B && b[2]==0x05 && b[7]==0xC3) {
                fingerprint_ok=1;
                using Getter=void* (__cdecl*)();
                Getter fn=reinterpret_cast<Getter>(getter);
                void* factory=fn();
                result_nonnull=(factory!=nullptr);
                // DO NOT DEREFERENCE factory OR RETAIN the pointer.
            }
        }
    }
#endif
    fprintf(output,
            "module_found\texport_found\tcode_fingerprint_ok\tfactory_pointer_nonnull\n"
            "%d\t%d\t%d\t%d\n",
            module_found,export_found,fingerprint_ok,result_nonnull);
    fclose(output);
    s.UtilitySuite3()->AEGP_ReportInfo(g_id,
            "ShapeLayerAE: Private getter probe recorded to TEMP (read-only).");
    return A_Err_NONE;
}

'''
sub(before,private+before)
sub("""    if (already_handled || (command != g_command && command != g_unknown_command))
        return A_Err_NONE;
    if (handled) *handled = TRUE;
    return DumpActiveLayer(command == g_unknown_command);""",
"""    if (already_handled) return A_Err_NONE;
    if (command == g_private_command) {
        if (handled) *handled = TRUE;
        return ProbePrivateTDBFactoryGetter();
    }
    if (command != g_command && command != g_unknown_command)
        return A_Err_NONE;
    if (handled) *handled = TRUE;
    return DumpActiveLayer(command == g_unknown_command);""")
sub("""    if (layer) {
        s.CommandSuite1()->AEGP_EnableCommand(g_unknown_command);""",
"""    s.CommandSuite1()->AEGP_EnableCommand(g_private_command);
    if (layer) {
        s.CommandSuite1()->AEGP_EnableCommand(g_unknown_command);""")
sub("""    if (!err) err = s.RegisterSuite5()->AEGP_RegisterCommandHook(
        g_id, AEGP_HP_BeforeAE, AEGP_Command_ALL, CommandHook, nullptr);""",
"""    if (!err) err = s.CommandSuite1()->AEGP_GetUniqueCommand(&g_private_command);
    if (!err) err = s.CommandSuite1()->AEGP_InsertMenuCommand(
        g_private_command, "ShapeLayerAE: Probe Private TDB Getter (Read Only)",
        AEGP_Menu_ANIMATION, AEGP_MENU_INSERT_AT_TOP);
    if (!err) err = s.RegisterSuite5()->AEGP_RegisterCommandHook(
        g_id, AEGP_HP_BeforeAE, AEGP_Command_ALL, CommandHook, nullptr);""")
p.write_text(s,encoding="utf-8")
print("UPGRADED",p,len(s.splitlines()))
