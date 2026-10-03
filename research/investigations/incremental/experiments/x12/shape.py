import sys, collections
src = "/home/user/sg-style/build/oracle/layout/%s.chromium.tsv"
for page in ("ecma262","html5","apollo11"):
    parent=[]
    for line in open(src%page):
        if line.startswith("E\t"):
            f=line.split("\t",5)
            parent.append(int(f[3]))
    n=len(parent)
    roots=[i for i,p in enumerate(parent) if p<0]
    assert all(p<i for i,p in enumerate(parent) if p>=0), "not doc order"
    depth=[0]*n
    kids=collections.Counter()
    for i,p in enumerate(parent):
        if p>=0:
            depth[i]=depth[p]+1; kids[p]+=1
    leaves=n-len(kids)
    top=kids.most_common(4)
    hist=collections.Counter(depth)
    avgd=sum(depth)/n
    print(page,"n",n,"roots",roots[:3],len(roots),"maxdepth",max(depth),"avgdepth %.2f"%avgd,"leaves",leaves,"maxfan",top)
    with open("%s.parents"%page,"w") as o:
        o.write("%d\n"%n)
        for p in parent:
            o.write("%d\n"%(n if p<0 else p))
