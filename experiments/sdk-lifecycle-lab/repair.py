"""Pinned SmartyPants render-state ownership repair and source-extracted tests.

Only this package's workbench, patches and results are written. No plug-in is
installed and no After Effects host is launched. repair_smarty(bytes) is the
public composition API; it edits only exact preimages inside ActuallyRender.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
DEFAULT_SDK = Path("E:/ae25.6_61.64bit.AfterEffectsSDK/Examples")
LOCKS = {
    "SmartyPants.cpp": ("Effect/SmartyPants/SmartyPants.cpp", "4865f3d8db8de37f5109cb34fdf04b7ae8f5b5582f12f490baa67f7f179104c2"),
    "SmartyPants.h": ("Effect/SmartyPants/SmartyPants.h", "842b1fd4f3366ce456b3b7a0e6ec9edf032aef08f90cf9d06b21dc4e83c4f654"),
    "AE_Effect.h": ("Headers/AE_Effect.h", "215d07b840ef2c731d2394f00edad40d05cc23ec33d0a001b19a1468cf662faf"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_path(path: Path) -> Path:
    result = path.resolve()
    if HERE.resolve() not in result.parents:
        raise ValueError("destination escapes lifecycle package")
    return result


def function_span(source: str, name: str) -> tuple[int, int]:
    matches = list(re.finditer(r"static\s+PF_Err\s+" + re.escape(name) + r"\s*\(", source))
    if len(matches) != 1:
        raise ValueError(f"function {name} missing or ambiguous")
    start = matches[0].start()
    cursor = source.index("{", matches[0].end()) + 1
    depth = 1
    while depth and cursor < len(source):
        depth += (source[cursor] == "{") - (source[cursor] == "}")
        cursor += 1
    if depth:
        raise ValueError(f"unterminated function {name}")
    return start, cursor


def extract_function(source: str, name: str) -> str:
    start, end = function_span(source, name)
    return source[start:end]


def repair_smarty(source: bytes, *, reverse: bool = False) -> bytes:
    """Compose this ownership change with independent edits in other functions.

    This transformation is source-anchored, not a whole-file provenance check.
    The standalone run separately validates LOCKS; composition callers must
    validate their own base corpus and record their intervening transformations.
    """
    text = source.decode("utf-8")
    start, end = function_span(text, "ActuallyRender")
    body = text[start:end]
    newline = "\r\n" if "\r\n" in body else "\n"
    edits = [
        ("\tSmartyPantsData\t\t*id;",
         "\tSmartyPantsData\t\trender_data{};" + newline +
         "\tSmartyPantsData\t\t*id = &render_data;"),
        ("\tif (!in_data->sequence_data) {" + newline +
         "\t\tPF_COPY(input, output, &src_rect, NULL);" + newline +
         "\t\terr = PF_Err_INTERNAL_STRUCT_DAMAGED;" + newline +
         "\t}" + newline,
         "\t// Render parameters belong to this invocation; MFR sequence_data may be NULL." + newline),
        (newline + "\t\tid = (SmartyPantsData*)*(in_data->sequence_data);",
         newline + "\t\tid->channel = channel_paramP->u.pd.value;"),
    ]
    for before, after in reversed(edits) if reverse else edits:
        if reverse:
            before, after = after, before
        if body.count(before) != 1:
            raise ValueError("ActuallyRender patch preimage missing or ambiguous")
        body = body.replace(before, after, 1)
    return (text[:start] + body + text[end:]).encode("utf-8")


def extract_definitions(header: str) -> str:
    definitions = []
    for name in ("SmartyPantsData", "SmartyPantsDataPlus"):
        pattern = r"typedef\s+struct\s*\{[^{}]*\}\s*" + name + r";"
        matches = re.findall(pattern, header)
        if len(matches) != 1:
            raise ValueError(f"missing or ambiguous {name} declaration")
        definitions.append(matches[0])
    channels = re.findall(r"enum\s*\{\s*Channel_RGB\s*=\s*1,.*?Channel_ALPHA\s*\};",
                          header, re.S)
    if len(channels) != 1:
        raise ValueError("missing channel enumeration")
    return "\n".join(definitions + channels)


def extracted_harness(source: bytes, header: bytes, effect: bytes) -> bytes:
    source_text = source.decode("utf-8")
    template = (HERE / "harness.cpp.in").read_text("utf-8")
    kernel = extract_function(source_text, "InvertPixel8")
    alpha = re.search(r"case Channel_ALPHA:\s*(.*?)\s*break;", kernel, re.S)
    maximum = re.search(r"^#define\s+PF_MAX_CHAN8\s+([^\r\n/]+)",
                        effect.decode("utf-8"), re.M)
    if alpha is None or maximum is None:
        raise ValueError("missing original 8-bit Alpha expression or maximum")
    replacements = {
        "// SDK_DEFINITIONS": extract_definitions(header.decode("utf-8")),
        "// ALPHA8_BODY": alpha.group(1),
        "// ACTUALLY_RENDER": extract_function(source_text, "ActuallyRender"),
        "// SDK_MAXIMUM": "constexpr int PF_MAX_CHAN8 = " + maximum.group(1).strip() + ";",
    }
    for marker, value in replacements.items():
        if template.count(marker) != 1:
            raise ValueError("missing or ambiguous harness insertion marker")
        template = template.replace(marker, value)
    return template.encode("utf-8")


def write_bytes(path: Path, data: bytes):
    path = local_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def command(args: list[str], timeout: int = 120):
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise ValueError("command failed:\n" + result.stdout + "\n" + result.stderr)
    return result


def run(sdk_root: Path, compiler: str) -> dict:
    source_data = {}
    records = {}
    for name, (relative, expected) in LOCKS.items():
        path = sdk_root / relative
        data = path.read_bytes()
        if sha(data) != expected:
            raise ValueError(f"source hash changed: {path}")
        source_data[name] = data
        records[name] = {"path": str(path.resolve()), "sha256": sha(data)}
    original = source_data["SmartyPants.cpp"]
    repaired = repair_smarty(original)
    if repair_smarty(repaired, reverse=True) != original:
        raise ValueError("repair round trip failed")
    global_setup = extract_function(original.decode("utf-8"), "GlobalSetup")
    if "PF_OutFlag2_SUPPORTS_THREADED_RENDERING" not in global_setup:
        raise ValueError("source does not advertise the investigated MFR contract")
    header_text = source_data["AE_Effect.h"].decode("utf-8")
    if "in_data->sequence_data will be NULL during render" not in header_text:
        raise ValueError("pinned header no longer contains the investigated contract")
    # All existing source copies are checked before any copy is changed.
    destinations = []
    for variant, cpp in (("original", original), ("copy", repaired)):
        for name, data in (("SmartyPants.cpp", cpp),
                           ("SmartyPants.h", source_data["SmartyPants.h"])):
            path = local_path(HERE / "workbench" / variant / name)
            if path.exists() and path.read_bytes() != data:
                raise ValueError(f"unrecognized edits in working copy: {path}")
            destinations.append((path, data))
    for path, data in destinations:
        write_bytes(path, data)
    diff = "".join(difflib.unified_diff(
        original.decode().splitlines(keepends=True),
        repaired.decode().splitlines(keepends=True),
        fromfile="a/SmartyPants.cpp", tofile="b/SmartyPants.cpp"))
    write_bytes(HERE / "patches" / "SmartyPants.cpp.patch", diff.encode())

    reports = {}
    for variant, data in (("original", original), ("copy", repaired)):
        harness = extracted_harness(data, source_data["SmartyPants.h"],
                                    source_data["AE_Effect.h"])
        cpp = local_path(HERE / "workbench" / ("harness-" + variant + ".cpp"))
        exe = local_path(HERE / "workbench" / ("harness-" + variant + ".exe"))
        write_bytes(cpp, harness)
        build = command([compiler, "-std=c++17", "-O2", str(cpp), "-o", str(exe)])
        result = json.loads(command([str(exe)], timeout=60).stdout)
        result["harness_sha256"] = sha(harness)
        result["source_sha256"] = sha(data)
        full_source = local_path(HERE / "workbench" / variant / "SmartyPants.cpp")
        syntax_command = [compiler, "-std=c++17", "-fsyntax-only",
                          "-DMSWindows", "-DWIN32", "-D_WINDOWS", str(full_source)]
        syntax_command.extend("-I" + str(sdk_root / part) for part in (
            "Headers", "Headers/SP", "Headers/Win", "Resources", "Util",
            "Effect/SmartyPants"))
        checked = command(syntax_command)
        write_bytes(HERE / "results" / ("syntax-" + variant + ".log"),
                    checked.stderr.encode())
        result["whole_source_syntax"] = {
            "exit_code": checked.returncode,
            "warning_count": checked.stderr.count("warning:"),
            "command": syntax_command,
            "scope": "actual SDK headers, syntax only; not linked or run in AE"}
        reports[variant] = result
    old, new = reports["original"], reports["copy"]
    assert old["null_sequence"]["error"] != 0
    assert old["null_sequence"]["output_alpha"] == 64
    assert new["null_sequence"]["error"] == 0
    assert new["null_sequence"]["output_alpha"] == 191
    assert new["null_sequence"]["kernel_calls"] == 1
    assert old["nested_shared_handle"]["outer_alpha"] == 127
    assert old["nested_shared_handle"]["same_parameter_storage"]
    assert new["nested_shared_handle"]["outer_alpha"] == 191
    assert not new["nested_shared_handle"]["same_parameter_storage"]
    assert new["nested_shared_handle"]["outer_blend"] == 0
    assert new["nested_shared_handle"]["inner_blend"] == 128
    assert new["nested_shared_handle"]["shared_storage_unchanged"]
    assert new["sequential"]["case_failures"] == 0
    assert new["nested_channels"]["outer_channel"] == new["nested_channels"]["expected_channel"]
    assert old["nested_channels"]["outer_channel"] != old["nested_channels"]["expected_channel"]
    for name, (relative, expected) in LOCKS.items():
        if sha((sdk_root / relative).read_bytes()) != expected:
            raise ValueError(f"original SDK changed while running: {name}")
    version = command([compiler, "--version"]).stdout.splitlines()[0]
    report = {
        "issue": "F-THREAD-004", "schema": 1,
        "scope": "full source-extracted ActuallyRender under a mock SDK backend",
        "normative_case": "MFR render input sequence_data is NULL (AE_Effect.h:926-927)",
        "conditional_case": "sequential nested invocations sharing a non-NULL handle; not a claimed AE scheduling trace",
        "ae_host_executed": False, "concurrent_cpp_data_race_executed": False,
        "original_sdk_modified": False, "compiler": compiler,
        "compiler_version": version, "sources": records, "results": reports,
    }
    write_bytes(HERE / "results" / "summary.json",
                (json.dumps(report, indent=2) + "\n").encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--compiler", default=shutil.which("clang++"))
    args = parser.parse_args()
    try:
        if not args.compiler:
            raise ValueError("clang++ unavailable; supply --compiler")
        report = run(args.sdk_root, args.compiler)
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, OSError, AssertionError, subprocess.TimeoutExpired) as exc:
        print("error: " + str(exc).encode("ascii", "backslashreplace").decode())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
