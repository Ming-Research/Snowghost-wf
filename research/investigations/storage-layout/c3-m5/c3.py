"""Interleaved C3 timing of macOS layout_oracle drivers on the M5 Air.

Scratch helper, run only under Whitefoot's host lock. For each round, each
build in BUILDS order runs each mode once at REPS and once at 0 repetitions;
the per-run time is (T(REPS) - T(0)) / REPS, as layout/run.sh computes it.
Two names for one driver give the noise control. Prints one line per
measurement and a summary of the best round per cell.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "renderer/style/ua.css"
D = "build/research/concurrency"
PAGES = {
    "html5": [f"{D}/html5.html"],
    "ecma262": [f"{D}/ecma262.html",
                f"assets/css/ecmarkup.css={D}/ecma262-ecmarkup.css",
                f"assets/css/print.css={D}/ecma262-print.css"],
}


def elapsed(binary, mode, reps, page, workers):
    args = [binary, mode, str(reps), page[0], UA] + page[1:]
    env = dict(os.environ)
    if workers:
        env["WF_WORKERS"] = str(workers)
    start = time.perf_counter()
    done = subprocess.run(args, cwd=HERE, env=env, stdout=subprocess.DEVNULL,
                          stderr=subprocess.PIPE)
    took = time.perf_counter() - start
    if done.returncode != 0:
        sys.exit(f"{' '.join(args)} failed: {done.stderr.decode()[:400]}")
    return took


def main():
    builds = sys.argv[1].split()          # name=driver-name pairs
    pages = sys.argv[2].split()
    modes = [m.split(":")[0] for m in sys.argv[3].split()]
    reps_of = {m.split(":")[0]: int(m.split(":")[1]) for m in sys.argv[3].split()}
    rounds = int(sys.argv[5])
    lanes = sys.argv[6].split()           # seq and/or par4
    rows = []
    for pair in builds:
        name, driver = pair.split("=")
        for lane in lanes:
            suffix = "par" if lane == "par4" else "seq"
            for page in pages:
                elapsed(os.path.join(HERE, "drivers", f"{driver}-{suffix}"), modes[0], 0, PAGES[page], 4 if lane == "par4" else 0)
    for rnd in range(1, rounds + 1):
        for page in pages:
            for mode in modes:
                for lane in lanes:
                    for pair in builds:
                        name, driver = pair.split("=")
                        suffix = "par" if lane == "par4" else "seq"
                        binary = os.path.join(HERE, "drivers", f"{driver}-{suffix}")
                        workers = 4 if lane == "par4" else 0
                        reps = reps_of[mode]
                        zero = elapsed(binary, mode, 0, PAGES[page], workers)
                        full = elapsed(binary, mode, reps, PAGES[page], workers)
                        per = (full - zero) / reps
                        row = dict(round=rnd, page=page, mode=mode, lane=lane,
                                   build=name, zero=zero, full=full, per=per)
                        rows.append(row)
                        print(json.dumps(row), flush=True)
    best = {}
    for r in rows:
        k = (r["page"], r["mode"], r["lane"], r["build"])
        best[k] = min(best.get(k, 1e9), r["per"])
    print("SUMMARY best per-run seconds")
    for k in sorted(best):
        print(" ".join(k), f"{best[k]:.4f}")


if __name__ == "__main__":
    main()
