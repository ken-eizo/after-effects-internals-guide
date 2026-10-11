"""Compile both complete SmartyPants translation units using installed SDK headers."""
import json
from pathlib import Path
import shutil
import subprocess
import repair


def main():
    provenance = json.loads((repair.WORK / "provenance.json").read_text("utf-8"))
    sdk = Path(json.loads((repair.HERE / "source-lock.json").read_text("utf-8"))["sdk_default"])
    compiler = shutil.which("clang++")
    if not compiler:
        raise SystemExit("clang++ not available")
    reports = {}
    for variant in ["original", "copy"]:
        source = repair.WORK / variant / "SmartyPants.cpp"
        expected = provenance["SmartyPants.cpp"]["sha256" if variant == "original" else "repaired_sha256"]
        if repair.sha(source.read_bytes()) != expected:
            raise SystemExit("unexpected source hash")
        command = [compiler, "-std=c++17", "-fsyntax-only", "-DMSWindows", "-DWIN32", "-D_WINDOWS", str(source)]
        command.extend("-I" + str(sdk / part) for part in
                       ["Headers", "Headers/SP", "Headers/Win", "Resources", "Util", "Effect/SmartyPants"])
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=120)
        reports[variant] = {
            "command": command, "returncode": run.returncode, "source_sha256": repair.sha(source.read_bytes()),
            "warning_count": run.stderr.count("warning:"),
            "diagnostics_sha256": repair.sha(run.stderr.encode()),
            "scope": "whole translation unit, actual SDK headers; syntax only; no link or host execution",
        }
        (repair.HERE / "results").mkdir(exist_ok=True)
        (repair.HERE / "results" / ("syntax-" + variant + ".log")).write_text(run.stderr, encoding="utf-8")
        if run.returncode:
            raise SystemExit(run.stderr.encode("ascii", "backslashreplace").decode())
    (repair.HERE / "results" / "syntax-check.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
