#!/bin/sh
# usage: runlock.sh PAGE N_PER_KIND WORKERS CHUNK  -- runs run.py in chunks, each under the host lock
cd /tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x1x3
page=$1; n=$2; w=$3; chunk=$4
while :; do
  CHUNK=$chunk perl /home/user/wf-pin/.github/run-check.pl x1-$page python3 run.py $page $n $w >> logs-$page.txt 2>&1
  rc=$?
  if [ $rc -eq 75 ]; then sleep 2; continue; fi
  if tail -3 logs-$page.txt | grep -q "^0 edits to run"; then echo ALLDONE >> logs-$page.txt; break; fi
  if [ $rc -ne 0 ]; then echo "rc=$rc" >> logs-$page.txt; sleep 5; fi
done
