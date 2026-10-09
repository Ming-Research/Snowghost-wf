"""Temporary hosted-only FN-1 migration probe; removed after collecting its patch.

Checks each gate module, records exact refusals, and deletes only simple
compiler-reported unreachable tails in the disposable runner checkout.
The exported patch is inspected before any source change is committed.
Other diagnostics stop that module; the remaining modules are still checked.
"""
import json
from pathlib import Path
import re
import subprocess
import time

root = Path.cwd()
renderer = root / "renderer"
out = root / "build/fn1-diagnostics"
out.mkdir(parents=True, exist_ok=True)
compiler = root / "build/whitefoot/wf-64c0f956df63/whitefootc"
modules = re.findall(r"^(pkg[a-z_:]*):", (renderer / "modules.wfg").read_text(), re.M)
# The smallest useful sample is the previously refused normalization module.
modules.remove("pkg::text::normalization")
modules.insert(0, "pkg::text::normalization")
locations = {}
records = []
results = []
for module in modules:
    started = time.monotonic()
    for attempt in range(100):
        run = subprocess.run([str(compiler), "--cache", str(out / "cache"),
                              "--fragments", "function", "--graph", "modules.wfg",
                              "--check-module", module], cwd=renderer,
                             capture_output=True, text=True)
        log = run.stdout + run.stderr
        (out / f"{module.replace('::', '-')}-{attempt}.txt").write_text(log)
        if run.returncode == 0:
            results.append({"module": module, "result": "accepted", "attempts": attempt + 1,
                            "seconds": time.monotonic() - started})
            break
        match = re.search(r"(\./[^\s:]+\.wf):(\d+):(\d+): error\[FN-1\]: UnreachableStatement", log)
        if not match:
            results.append({"module": module, "result": "other refusal", "diagnostic": log,
                            "seconds": time.monotonic() - started})
            break
        path = renderer / match[1]
        index = int(match[2]) - 1
        lines = path.read_text().splitlines(keepends=True)
        source = lines[index].strip()
        # Leave any statement whose extent is not trivial for manual inspection.
        if not re.fullmatch(r"(?:return|let)\b[^{};]*;", source):
            results.append({"module": module, "result": "manual FN-1", "diagnostic": log})
            break
        # FN-1 selects the first unreachable statement. Its remaining sibling
        # statements are unreachable too; remove the whole simple tail at once
        # so a deleted binder cannot create an unrelated name-resolution error.
        end = index
        indent = len(lines[index]) - len(lines[index].lstrip())
        while end < len(lines):
            tail = lines[end].strip()
            if tail == "}":
                break
            if not re.fullmatch(r"(?:return|let)\b[^{};]*;", tail) or len(lines[end]) - len(lines[end].lstrip()) != indent:
                end = index
                break
            end += 1
        if end == index:
            results.append({"module": module, "result": "manual FN-1 tail", "diagnostic": log})
            break
        original = locations.setdefault(str(path.relative_to(root)), list(range(1, len(lines) + 1)))
        function = re.findall(r"^fn (\w+)", "".join(lines[:index]), re.M)[-1]
        records.append({"module": module, "path": str(path.relative_to(root)),
                        "line": original[index], "function": function, "source": source,
                        "tail": [{"line": original[k], "source": lines[k].strip()} for k in range(index, end)],
                        "diagnostic": log})
        del lines[index:end]
        del original[index:end]
        path.write_text("".join(lines))
    else:
        raise RuntimeError(f"Too many refusals in {module}")
    (out / "deletions.json").write_text(json.dumps(records, indent=2) + "\n")
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results[-1]), flush=True)
    if module == "pkg::text::normalization":
        # One module established the check's scale before the full batch.
        print("Normalization sample complete; checking the remaining gate modules.", flush=True)
(out / "adaptation.patch").write_text(subprocess.run(
    ["git", "diff", "--", "renderer"], capture_output=True, text=True, check=True).stdout)
print(f"Recorded {len(records)} FN-1 tails; inspect adaptation.patch before applying.")
