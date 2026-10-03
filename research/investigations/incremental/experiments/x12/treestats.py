import collections
for page in ("html5","ecma262","apollo11"):
    f=open(page+".parents"); n=int(f.readline()); parent=[int(x) for x in f]
    pos=[0]*n; cnt=collections.Counter(); depth=[0]*n; scan=[0]*n
    for i,p in enumerate(parent):
        if p<n:
            cnt[p]+=1; pos[i]=cnt[p]; depth[i]=depth[p]+1; scan[i]=scan[p]+pos[i]
    ss=sorted(scan); 
    tgt=max(range(n),key=lambda i:scan[i])
    print(page,"n",n,"avg depth %.2f max %d"%(sum(depth)/n,max(depth)),"scan(children compared on path): mean %.0f median %d p99 %d max %d at node %d depth %d"%(sum(scan)/n,ss[n//2],ss[int(n*.99)],ss[-1],tgt,depth[tgt]))
