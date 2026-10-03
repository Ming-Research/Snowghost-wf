import re, collections
def load(f):
    d={}
    for line in open(f):
        if "per-rep" not in line or line.startswith(("==","real")): continue
        p=line.rstrip("\n").split("\t")
        d[p[0]]=float(re.search(r"per-rep ([\d.]+) us",line).group(1))
    return d
R=load("record.raw"); V=load("validate.raw"); S=load("scan.raw"); T=load("tree.raw")
PAGES={"html5":(13843,60868),"ecma262":(10217,57514),"apollo11":(1113,2569)}
# full build (style+layout, from efficiency.txt of the earlier round; seconds)
FULL={"html5":(3.414,1.308,0.59),"ecma262":(3.726,1.5127,0.5867),"apollo11":(1.100,0.3255,0.044)}  # seq, par4 style+layout, par4 layout only
print("RECORDING (k=10, record minus plain, seq / par-1)")
for page,(cx,pa) in PAGES.items():
    for grain,n in (("contexts",cx),("paragraphs",pa)):
        edges=n*10
        pl=R["plain %s %s seq"%(page,grain)]; rc=R["append-id+ver %s %s seq"%(page,grain)]; fl=R["flat-ids %s %s seq"%(page,grain)]
        pl1=R["plain %s %s par-1"%(page,grain)]; rc1=R["append-id+ver %s %s par-1"%(page,grain)]
        d=rc-pl; d1=rc1-pl1
        fs,f4,l4=FULL[page]
        print("%-9s %-10s n %6d edges %7d plain %8.1f us  append %8.1f us  delta seq %7.1f us (%.2f ns/edge) par-1 %7.1f us (%.2f ns/edge) | flat delta %6.1f | all-in append %.2f ns/edge | %% of full seq %.3f  %% of par4 style+layout %.3f %% of par4 layout %.3f"%(
            page,grain,n,edges,pl,rc,d,d*1000/edges,d1,d1*1000/edges,fl-pl,rc*1000/edges,100*d/1e6/fs,100*d/1e6/f4,100*d/1e6/l4))
print()
print("ALL-IN RECORD as upper bound, recorded serially (not split by the compiler): share of par4 full build")
for page,(cx,pa) in PAGES.items():
    fs,f4,l4=FULL[page]
    for grain,n in (("contexts",cx),("paragraphs",pa)):
        rc=R["append-id+ver %s %s par-4"%(page,grain)]
        print(page,grain,"append par-4 %.1f us"%rc, "= %.3f%% of par4 style+layout, %.3f%% of par4 layout"%(100*rc/1e6/f4,100*rc/1e6/l4))
print()
print("break-even edges per unit for 5 percent of par4 style+layout, using all-in ns/edge")
for page,(cx,pa) in PAGES.items():
    fs,f4,l4=FULL[page]
    for grain,n in (("contexts",cx),("paragraphs",pa)):
        rc=R["append-id+ver %s %s seq"%(page,grain)]; per=rc*1000/(n*10)
        be=0.05*f4*1e9/per/n
        print(page,grain,"all-in %.2f ns/edge -> 5%% of par4 s+l at %.0f edges per unit; at recalled 100 ns: %.1f%% at 10/unit"%(per,be,100*n*10*100e-9/f4))
print()
print("SCAN (dense version array, seq / par-4, us)")
for page in PAGES:
    print(page," ".join("%s %.1f/%.1f"%(g,S["scan %s %s seq"%(page,g)],S["scan %s %s par-4"%(page,g)]) for g in ("elements","paragraphs","contexts")))
print()
print("VALIDATE (us) seq / par-4")
for page in PAGES:
    for g in ("contexts","paragraphs"):
        print(page,g," ".join("%s %.1f/%.1f"%(k,V["%s %s %s seq"%(k,page,g)],V["%s %s %s par-4"%(k,page,g)]) for k in ("validate-dense-edges","memo-lookup+edges","memo-lookup-only")))
print()
print("TREE (us per frame)")
for page in PAGES:
    b=T["tree %s seq"%page] if False else None
