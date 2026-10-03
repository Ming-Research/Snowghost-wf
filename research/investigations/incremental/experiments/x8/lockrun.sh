#!/bin/sh
# lockrun.sh LABEL CMD...  : run CMD under the host lock, retrying while another command owns it
label=$1; shift
while :; do
  out=$(perl /home/user/wf-pin/.github/run-check.pl "$label" "$@" 2>&1); rc=$?
  case "$out" in *"already owned by another command"*) sleep 10; continue;; esac
  printf '%s\n' "$out"; exit $rc
done
