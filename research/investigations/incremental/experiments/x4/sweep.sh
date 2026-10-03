#!/bin/sh
# sweep.sh PAGE : dump PAGE at each viewport width with the width-taking driver (run from the sg-html5 root, under the host lock)
page=$1
cd /home/user/sg-html5
data=build/research/concurrency
case $page in
  ecma262) sheets="assets/css/ecmarkup.css=$data/ecma262-ecmarkup.css assets/css/print.css=$data/ecma262-print.css" ;;
  html5) sheets="" ;;
  apollo11) sheets="wikibase.client.init&only=styles&skin=vector-2022=$data/apollo11-modules.css modules=site.styles&only=styles&skin=vector-2022=$data/apollo11-site.css" ;;
esac
out=/tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x4/dumps
for w in ${WIDTHS:-1280 1270 1290 1275 1285 1279 1281 1260 1300 1250 1310 1230 1330 1200 1360 1150 1400 1100}; do
  s=$(date +%s.%N)
  build/layout_oracle_x4 dump $w $data/$page.html renderer/style/ua.css $sheets > $out/$page.$w.tsv || echo "FAILED $page $w"
  e=$(date +%s.%N)
  echo "$page $w $(echo "$e - $s" | bc) s $(wc -l < $out/$page.$w.tsv) lines"
done
