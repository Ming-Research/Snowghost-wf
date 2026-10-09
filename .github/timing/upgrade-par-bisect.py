"""Temporary hosted capture, called only by upgrade-par-bisect.yml.

Use the established nested-mode harness rather than a new timing path.
The pilot chooses three rounds when twin ratio noise is <= 0.15, otherwise
five (the bounded maximum). A release-level loss requires non-overlapping
round/twin ratio ranges; overlapping ranges reject a localized boundary.
No elapsed result is used as a correctness oracle.
"""

import csv
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import time


root = Path.cwd()
results = root / "results"
raw = results / "timings"
raw.mkdir()
with (results / "builds.tsv").open() as stream:
    builds = list(csv.DictReader(stream, delimiter="\t"))
names = [row["name"] for row in builds]
pages = ("ecma262", "html5")
observations = []


def capture(round_number):
    order = names if round_number % 2 else list(reversed(names))
    with (results / "order.txt").open("a") as out:
        out.write(f"round {round_number}: {' '.join(order)}\n")
    started = time.monotonic()
    for name in order:
        tree = root / "build/trees" / name
        for binary in ("layout_oracle", "layout_oracle_par"):
            shutil.copy2(tree / "build" / binary, root / "build" / binary)
        pin = next(row["release"] for row in builds if row["name"] == name)
        env = dict(os.environ, BUILT="1", RUNS="1", WORKERS="4",
                   MODES="boxes text layout", WF_WORKERS="4",
                   WHITEFOOTC=str(tree / "build/whitefoot" / pin / "whitefootc"))
        for page in pages:
            path = raw / f"{name}-{page}-r{round_number}.txt"
            error_path = path.with_suffix(".stderr")
            sample_started = time.monotonic()
            with path.open("w") as out, error_path.open("w") as error:
                process = subprocess.run(
                    ["sh", "research/investigations/layout/run.sh", "time", page, "3"],
                    env=env, stdout=out, stderr=error, timeout=300, check=False)
            path.with_suffix(".exit").write_text(f"{process.returncode}\n")
            print(f"round {round_number} {name} {page}: wall {time.monotonic() - sample_started:.1f}s", flush=True)
            print(path.read_text(), flush=True)
            if process.returncode:
                raise SystemExit(f"harness failed: {error_path.read_text()}")
            values = {}
            for line in path.read_text().splitlines():
                fields = line.split()
                if len(fields) == 7 and fields[0] == page:
                    mode, lane = fields[1:3]
                    if (mode, lane) in values:
                        raise SystemExit(f"duplicate mode/lane in {path}: {mode} {lane}")
                    # Recompute from retained T(0), T(REPS) at full precision.
                    values[mode, lane] = (float(fields[5]) - float(fields[4])) / int(fields[3])
            if set(values) != {(mode, lane) for mode in ("boxes", "text", "layout") for lane in ("seq", "par-4")}:
                raise SystemExit(f"missing or duplicate modes in {path}")
            for part, upper, lower in (("text", "text", "boxes"), ("layout-passes", "layout", "text")):
                seq = values[upper, "seq"] - values[lower, "seq"]
                par = values[upper, "par-4"] - values[lower, "par-4"]
                if seq <= 0 or par <= 0:
                    raise SystemExit(f"nonpositive nested difference: {name} {page} {part}: {seq}, {par}")
                observations.append(dict(round=round_number, name=name, page=page,
                                         part=part, seq=seq, par4=par, ratio=par / seq))
    return time.monotonic() - started


def save():
    with (results / "parts.csv").open("w") as out:
        writer = csv.DictWriter(out, fieldnames=("round", "name", "page", "part", "seq", "par4", "ratio"))
        writer.writeheader()
        writer.writerows(observations)
    lines = ["Seconds are medians across rounds; ratios are medians of paired round ratios.",
             "", "| Page | Build | Part | Seq s | Par-4 s | Ratio median [min, max] |",
             "|---|---|---|---:|---:|---:|"]
    for page in pages:
        for name in names:
            for part in ("text", "layout-passes"):
                rows = [r for r in observations if (r["name"], r["page"], r["part"]) == (name, page, part)]
                ratios = [r["ratio"] for r in rows]
                lines.append(f"| {page} | {name} | {part} | {statistics.median(r['seq'] for r in rows):.4f} | {statistics.median(r['par4'] for r in rows):.4f} | {statistics.median(ratios):.3f} [{min(ratios):.3f}, {max(ratios):.3f}] |")
    (results / "summary.md").write_text("\n".join(lines) + "\n")


pilot_seconds = capture(1)
save()
noise = []
for page in pages:
    for pin in dict.fromkeys(row["release"] for row in builds):
        for part in ("text", "layout-passes"):
            ratios = [r["ratio"] for r in observations if r["name"].startswith(pin[3:] + "-") and r["page"] == page and r["part"] == part]
            if len(ratios) != 2:
                raise SystemExit("pilot requires exactly two independently compiled twins")
            noise.append((abs(ratios[0] - ratios[1]), page, pin, part, ratios))
worst = max(noise)
rounds = 3 if worst[0] <= 0.15 else 5
selection = f"Pilot round wall seconds: {pilot_seconds:.1f}\nWorst twin ratio difference: {worst}\nSelected total rounds: {rounds}; threshold 0.15, bounded maximum 5\n"
(results / "pilot-selection.txt").write_text(selection)
print(selection, flush=True)
if pilot_seconds > 1200:
    raise SystemExit("pilot exceeds the bounded timing budget; do not scale")
for number in range(2, rounds + 1):
    capture(number)
    save()
print((results / "summary.md").read_text(), flush=True)
