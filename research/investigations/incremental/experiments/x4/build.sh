#!/bin/sh
cd /home/user/sg-html5/renderer
while :; do
  perl /home/user/wf-pin/.github/run-check.pl x4-build /home/user/wf-pin/compiler/target/gate/whitefootc --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle_x4 > /tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x4/build.log 2>&1
  if [ -x ../build/layout_oracle_x4 ]; then break; fi
  sleep 20
done
echo finished
