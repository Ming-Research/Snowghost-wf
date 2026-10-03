import json,glob,sys,statistics
d=sys.argv[1]
rs=[json.load(open(f)) for f in sorted(glob.glob(d+'/*.json'))]
cols=[('elements',lambda r:r['census']['R']['elements']),('stacking',lambda r:r['census']['R']['stacking']),('transform',lambda r:r['census']['R']['transform']),('opacity<1',lambda r:r['census']['R']['opacity']),('filter',lambda r:r['census']['R']['filter']),('backdrop',lambda r:r['census']['R']['backdrop']),('blend',lambda r:r['census']['R']['blend']),('fixed',lambda r:r['census']['R']['fixed']),('sticky',lambda r:r['census']['R']['sticky']),('scrollRoots',lambda r:r['census']['R']['scrollRoots']),('will-change',lambda r:r['census']['R']['willChange']),('video',lambda r:r['census']['R']['video']),('canvas',lambda r:r['census']['R']['canvas']),('anim',lambda r:r['census']['A']['running']),('anim:compositor',lambda r:r['census']['A']['compositor']),('anim:paint',lambda r:r['census']['A']['paint']),('anim:layout',lambda r:r['census']['A']['layout']),('layers',lambda r:(r.get('layers') or {}).get('total',0)),('layers drawing',lambda r:(r.get('layers') or {}).get('drawsContent',0))]
print('| page | '+' | '.join(c for c,_ in cols)+' |'); print('|'+'---|'*(len(cols)+1))
for r in rs:
    if 'census' not in r: print('|',r['name'],'| FAILED',r.get('error'),r.get('gotoErr')); continue
    print('| '+r['name']+' | '+' | '.join(str(f(r)) for _,f in cols)+' |')
def pct(v,p):
    v=sorted(v); 
    if not v: return 0
    i=min(len(v)-1,int(round(p*(len(v)-1)))); return v[i]
ok=[r for r in rs if 'census' in r]
print('\ndistribution over',len(ok),'pages: median / p90 / max')
for c,f in cols:
    v=[f(r) for r in ok]; print(f'  {c}: {statistics.median(v)} / {pct(v,0.9)} / {max(v)}')
print('\nX17')
tf=0;ta=0;tb=0;tns=0
for r in ok:
    x=r.get('x17',{}); fr=x.get('frames',[])
    n=len(fr); a=sum(1 for f in fr if f['A']); b=sum(1 for f in fr if f['B']); ns=sum(1 for f in fr if f['nsA'] or f['nsB'])
    adv=sum(1 for f in fr if f['advanced'])
    print(f"  {r['name']}: frames={n} advanced={adv} totalSteps={x.get('totalSteps')} capped={x.get('capped')} roots={x.get('roots')} {x.get('rootDescr')} nonscrolling-present={ns} interleavedA={a} interleavedB={b}")
    tf+=n;ta+=a;tb+=b;tns+=ns
print('  total frames',tf,'A',ta,'B',tb,'nonscrolling present',tns, 'A%', 100*ta/max(tf,1), 'B%', 100*tb/max(tf,1))
