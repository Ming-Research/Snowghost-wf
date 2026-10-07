"""Generate the minimal guarded-append cases consumed by layout-check CI.

Kept only while the owner-preserving Paged experiment needs this compiler
acceptance investigation; it changes no renderer source.
"""
from pathlib import Path

out = Path('build/paged-guard')
out.mkdir(parents=True, exist_ok=True)
for shape in ('Paged', 'Slots'):
    constructor = 'box_paged_new' if shape == 'Paged' else 'box_slots_new'
    for loop in (False, True):
        for grow in (False, True):
            name = f'{shape}-loop{int(loop)}-grow{int(grow)}'
            statement = '''      if values^.inner.len < values^.inner.cap {
        place_back(window: &values^.inner, value: 0_u64);
      }
'''
            if loop:
                statement = '      let start = values^.inner.len;\n      for (at in start..required) {\n' + ''.join('  ' + line + '\n' for line in statement.splitlines()) + '      }\n'
            growth = '''      if values^.inner.cap < required {
        GROW(cell: values, capacity: required);
      }
'''.replace('GROW', 'grow_paged' if shape == 'Paged' else 'grow') if grow else ''
            source = '''enum Store {
  Vacant();
  Pages(storage: Box<SHAPE<u64>>);
}

fn append(store: &Store, required: u64) -> result: unit writes(store) {
  doc "Checks a guarded append through an enum payload reference.";
  match store^ {
    Vacant() => {
    }
    Pages(storage: values) => {
GROWTHSTATEMENT    }
  }
  return unit;
}

fn main() -> result: unit pure {
  doc "Instantiates the guarded append without any other renderer code.";
  let values = CONSTRUCTOR::<u64>(capacity: 4_u64);
  let store = Store::Pages(storage: move values);
  append(store: &store, required: 8_u64);
  return unit;
}
'''.replace('SHAPE', shape).replace('CONSTRUCTOR', constructor).replace('GROWTH', growth).replace('STATEMENT', statement)
            (out / f'{name}.wf').write_text(source)
