# Binary size

How large the engine binary may be, and which binary the gate measures against that limit.

### decision engine-binary-within-ten-million-bytes
`make binary-size-check`, a test of the gate, fails when the engine binary is over 10 000 000 bytes; only the owner changes this limit.
- rejected: an agent proposed 10 MiB (10 485 760 bytes) as the limit; the owner rejected it, because it would pass a binary between 10 000 000 and 10 485 760 bytes, while the largest build uses only 44.8 percent of the stricter limit (data: `research/investigations/binary-size/README.md`).

### decision binary-size-counts-the-renderer-alone
While no release ships a shell, the size check measures the renderer binary alone.
- rejected: an agent proposed counting an estimate of the shell now; the owner rejected it, because the shell does not exist and cannot be measured, so the check would pass or fail on a guess.

### decision binary-size-judged-on-linux-unstripped
The check measures the Linux x86-64 build as linked, without stripping it, and CI runs it on Linux only.
- rejected: an agent proposed judging the macOS build; the owner rejected it, because the Linux build is 1.91 times the macOS build, so a check on macOS would pass a Linux build over the limit (data: `research/investigations/binary-size/README.md`).
- rejected: an agent proposed measuring the stripped binary; the owner rejected it, because stripping hides 10.7 percent of the Linux build behind a step the build does not run, which makes the check looser (data: `research/investigations/binary-size/README.md`).

### decision binary-size-stand-in-is-the-parallel-layout-oracle
Until an engine binary exists, the check measures `layout_oracle`, the driver of the whole page pipeline, built with `--par`.
- rejected: an agent proposed a sequential build or a smaller driver as the stand-in; the owner rejected it, because the parallel build is the largest one measured, half again the sequential one, so every other build meets a limit it meets (data: `research/investigations/binary-size/README.md`).
