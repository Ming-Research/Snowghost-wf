#!/usr/bin/env python3
# bench.py GROUP: best-of-RUNS wall time of the x12 program; per repetition = (T(REPS) - T(0)) / REPS.
# Run under one run-check.pl lock (see lockrun.sh); prints one TSV line per configuration.
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
SEQ = here + "/bin/x12_seq"; PAR = here + "/bin/x12_par"
RUNS = int(os.environ.get("RUNS", "5"))
TARGET_S = float(os.environ.get("TARGET_S", "0.6"))
def once(binary, workers, args):
    env = dict(os.environ)
    if workers: env["WF_WORKERS"] = str(workers)
    import time
    t = time.perf_counter()
    r = subprocess.run([binary] + [str(a) for a in args], cwd=here, env=env, capture_output=True, text=True)
    dt = time.perf_counter() - t
    return dt, r.returncode, r.stdout.strip()
def best(binary, workers, args, runs=RUNS):
    b = None; out = None
    for _ in range(runs):
        dt, rc, o = once(binary, workers, args)
        if rc != 0: raise SystemExit("exit %d for %s %s" % (rc, binary, args))
        if b is None or dt < b: b = dt
        out = o
    return b, out
def measure(label, binary, workers, test, size, extra, probe=100):
    d0, _ = best(binary, workers, [test, size, 0] + extra, 3)
    d1, _ = best(binary, workers, [test, size, probe] + extra, 3)
    per = max((d1 - d0) / probe, 1e-8)
    reps = int(min(max(TARGET_S / per, probe), 5000000))
    t0, _ = best(binary, workers, [test, size, 0] + extra)
    tr, out = best(binary, workers, [test, size, reps] + extra)
    print("%s\ttest %d\tsize %d\treps %d\tT0 %.4f\tTR %.4f\tper-rep %.3f us\tout %s" % (label, test, size, reps, t0, tr, (tr - t0) / reps * 1e6, out), flush=True)
CFG = {"seq": (SEQ, 0), "par-1": (PAR, 1), "par-4": (PAR, 4)}
PAGES = {  # elements, contexts, paragraphs
 "html5": (117179, 13843, 60868), "ecma262": (179471, 10217, 57514), "apollo11": (11845, 1113, 2569)}
group = sys.argv[1]
if group == "scan":
    for page, (el, cx, pa) in PAGES.items():
        for grain, n in (("elements", el), ("paragraphs", pa), ("contexts", cx)):
            for name in ("seq", "par-4"):
                b, w = CFG[name]; measure("scan %s %s %s" % (page, grain, name), b, w, 1, n, [])
elif group == "tree":
    tgt = {"html5": 103274, "ecma262": 126722, "apollo11": 8461}
    for page in ("html5", "ecma262", "apollo11"):
        for test in (2, 3, 4):
            for name in ("seq",):
                b, w = CFG[name]; measure("tree %s %s" % (page, name), b, w, test, 0, [page + ".parents", tgt[page]], probe=1000)
elif group == "record":
    for page, (el, cx, pa) in PAGES.items():
        for grain, n in (("contexts", cx), ("paragraphs", pa)):
            for test in (5, 7, 6):
                for name in ("seq", "par-1", "par-4"):
                    b, w = CFG[name]
                    measure("%s %s %s %s" % ("plain" if test == 5 else ("flat-ids" if test == 7 else "append-id+ver"), page, grain, name), b, w, test, n, [10])
elif group == "ksweep":
    for k in (1, 4, 10, 16):
        for test in (5, 6):
            measure("%s k=%d html5 paragraphs seq" % ("plain" if test == 5 else "append-id+ver", k), SEQ, 0, test, 60868, [k])
elif group == "validate":
    for page, (el, cx, pa) in PAGES.items():
        for grain, n in (("contexts", cx), ("paragraphs", pa)):
            for test in (8, 9, 10):
                for name in ("seq", "par-4"):
                    b, w = CFG[name]
                    measure("%s %s %s %s" % ({8: "validate-dense-edges", 9: "memo-lookup+edges", 10: "memo-lookup-only"}[test], page, grain, name), b, w, test, n, [10, 1])
    for test in (8, 9):
        measure("%s html5 paragraphs seq nochange" % {8: "validate-dense-edges", 9: "memo-lookup+edges"}[test], SEQ, 0, test, 60868, [10, 0])
