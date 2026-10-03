#!/bin/sh
# retry until the host lock is free and the build succeeds
cd /home/user/sg-text/renderer
while :; do
  perl /home/user/wf-pin/.github/run-check.pl x8-build /home/user/wf-pin/compiler/target/gate/whitefootc --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle_x8 > /tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x8/build.log 2>&1
  if [ -x ../build/layout_oracle_x8 ]; then break; fi
  sleep 15
done
echo finished >> /tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x8/build.log
