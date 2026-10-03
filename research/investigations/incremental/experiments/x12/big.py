# big.py: record vs plain at sizes beyond L2 (per-core 2 MiB) to see the cache-miss sensitivity of recording.
import sys
sys.argv = ["bench.py", "none"]
exec(open("bench.py").read().split("group = sys.argv[1]")[0])
for n in (200000, 1000000, 3000000):
    for test in (5, 6):
        measure("%s n=%d seq" % ("plain" if test == 5 else "append-id+ver", n), SEQ, 0, test, n, [10], probe=3)
