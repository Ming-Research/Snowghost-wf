#!/bin/sh
cd /tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x4
for p in html5 ecma262 apollo11; do
  ./lockrun.sh x4-sweep-$p ./sweep.sh $p > sweep-$p.log 2>&1
done
echo finished > sweep.done
