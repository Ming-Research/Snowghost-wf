import subprocess, sys, os
pages = sys.argv[1:] or ['apollo11','html5','ecma262']
for p in pages:
    for line in open(f'cuts-{p}.txt'):
        if line.startswith('0.'):
            f = line.split('\t'); pc = int(float(f[0])*100); el = int(f[2].split()[1])
            print('==', p, pc, 'cut element', el, flush=True)
            st_f = f'dumps/{p}.full.style.tsv'; st_t = f'dumps/{p}.{pc}.style.tsv'
            subprocess.run(['python3', 'prefix.py', f'dumps/{p}.full.layout.tsv', f'dumps/{p}.{pc}.layout.tsv', st_f, st_t, str(el), f'dumps/{p}.{pc}.changed.tsv'])
