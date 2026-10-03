import json, sys
FRAME = 16.667e-3
for page in sys.argv[1:]:
    d = json.load(open('results/x16.%s.json' % page))
    print('\n%s: edits over one frame (A) with the near part of their cost (cost-weighted share within viewport +-720, i.e. +-1080 of the edit point):\n' % page)
    print('| edit | kind | cost ms | near share | near part ms | far part ms |')
    print('|---|---|---:|---:|---:|---:|')
    for o in sorted(d, key=lambda o: -o['cost']):
        if o['cost'] > FRAME:
            sh = o['w1080'].get('cost')
            print('| %s | %s | %.1f | %.3f | %.1f | %.1f |' % (o['id'], o['kind'], o['cost'] * 1e3, sh, o['cost'] * sh * 1e3, o['cost'] * (1 - sh) * 1e3))
