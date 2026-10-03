#!/bin/sh
cd /tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x1x3
while :; do
  perl /home/user/wf-pin/.github/run-check.pl x1-timing sh -c 'python3 timing.py && ./wcost' > logs-timing.txt 2>&1
  rc=$?
  if [ $rc -eq 75 ]; then sleep 2; continue; fi
  echo "rc=$rc" >> logs-timing.txt; break
done
