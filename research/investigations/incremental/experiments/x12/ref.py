# ref.py N K REPS CHANGE: Python reference of validate_frames' mismatch total (modes 8 and 9) and of the record pass.
import sys
M=(1<<64)-1
def mix(u,j,salt):
    a=(u*11400714819323198485)&M; b=(j*14029467366897019727)&M
    c=a^b; d=c^salt; e=d>>29; f=d^e; g=(f*13787848793156543929)&M; h=g>>32
    return g^h
n,k,reps,change=map(int,sys.argv[1:5])
ids=[[ ] for _ in range(n)]
for u in range(n):
    last=None
    for j in range(k):
        o=mix(u,j,1)%n
        if o==last: continue
        ids[u].append(o); last=o
dep=[0]*n
for u in range(n):
    for o in ids[u]: dep[o]+=1
tot=0
if change:
    for r in range(reps):
        at=(r*7919+13)%n
        tot+=dep[at]
print(tot)
