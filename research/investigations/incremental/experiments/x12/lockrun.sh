#!/bin/sh
# lockrun.sh LABEL COMMAND...: run-check.pl, retried until the host-wide lock is free.
while :; do
  perl /home/user/wf-pin/.github/run-check.pl "$@"
  rc=$?
  [ $rc -ne 75 ] && exit $rc
  sleep 5
done
