"""Temporary hosted frame/frontier evidence parser; remove with root-frame-probe.

The oracle's independent edit/full comparator remains the correctness gate.
This checker validates diagnostic completeness and emits the unmodified ordinary
records for that established checker. It makes no latency or admission claim.
"""

import argparse
import json
from pathlib import Path


FIELDS = """edit phase parent slot kind element pseudo anonymous events width height
baseline content_raw flow_end has_baseline margin_top margin_right margin_bottom
margin_left space_available space_basis_width space_basis_height space_forced_width
space_forced_height space_shrink laid_available laid_basis_width laid_basis_height
laid_forced_width laid_forced_height laid_shrink frame_valid frame_content_left
frame_content_top frame_flow_width frame_definite frame_columned frame_column_count
frame_column_width frame_column_gap dirty restyled restyled_blocks restyled_block
marked_paragraphs marked_paragraph marked_children marked_child intrinsic_known
intrinsic_held intrinsic_basis min_content max_content held_min held_max
definite_free flow_definite_free has_out boundary_dirty reference_dense""".split()
BOOLS = set("""anonymous has_baseline space_shrink laid_shrink frame_valid
frame_columned dirty restyled intrinsic_known intrinsic_held definite_free
flow_definite_free has_out boundary_dirty reference_dense""".split())
UNSIGNED = set("""edit phase parent slot kind element pseudo events restyled_blocks
restyled_block marked_paragraphs marked_paragraph marked_children marked_child""".split())
CLEAN = ["dirty", "restyled", "restyled_blocks", "marked_paragraphs", "marked_children"]
EXPECTED = {(edit, phase) for edit in (1, 2) for phase in (0, 1, 2)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse(raw):
    snapshots = {}
    schemas = 0
    ordinary = []
    frame_lines = []
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        words = line.split()
        if words and words[0] == "flow_probe_schema":
            require(words[1:] == FIELDS, f"schema mismatch at line {line_number}")
            schemas += 1
            frame_lines.append(line)
        elif words and words[0] == "flow_probe":
            require(schemas > 0, f"record precedes schema at line {line_number}")
            require(len(words) == len(FIELDS) + 1, f"record width at line {line_number}")
            values = [int(word) for word in words[1:]]
            row = dict(zip(FIELDS, values))
            require(all(row[field] in (0, 1) for field in BOOLS), f"Boolean field at line {line_number}")
            require(all(row[field] >= 0 for field in UNSIGNED), f"unsigned field at line {line_number}")
            require(row["frame_valid"] == int(row["kind"] == 0), f"frame validity at line {line_number}")
            key = (row["edit"], row["phase"])
            slots = snapshots.setdefault(key, {})
            require(row["slot"] not in slots, f"duplicate context {key}/{row['slot']}")
            slots[row["slot"]] = row
            frame_lines.append(line)
        elif line.startswith("flow_probe"):
            raise ValueError(f"malformed diagnostic at line {line_number}")
        else:
            ordinary.append(line)
    require(set(snapshots) == EXPECTED, f"snapshot set differs: {sorted(snapshots)}")
    require(schemas == 6, f"expected six schemas, found {schemas}")
    reference = set(snapshots[(1, 0)])
    require(bool(reference), "empty context snapshot")
    for key, slots in snapshots.items():
        require(set(slots) == reference, f"live context set differs at {key}")
        roots = [row for row in slots.values() if row["parent"] == 4294967295]
        require(len(roots) == 1, f"expected one context root at {key}")
        for slot, row in slots.items():
            require(row["parent"] == 4294967295 or row["parent"] in slots, f"absent parent at {key}/{slot}")
            if key[1] == 0:
                require(all(row[field] == 0 for field in CLEAN), f"before snapshot has dirty marks at {key}/{slot}")
    stable_fields = [field for field in FIELDS if field not in ("edit", "phase")]
    for slot in reference:
        after = snapshots[(1, 2)][slot]
        before = snapshots[(2, 0)][slot]
        changed = [field for field in stable_fields if after[field] != before[field]]
        require(not changed, f"post1/before2 differs for {slot}: {changed}")
    return snapshots, "".join(ordinary), "".join(frame_lines)


def describe(snapshots):
    frame_fields = [field for field in FIELDS if field.startswith("frame_")]
    space_fields = [field for field in FIELDS if field.startswith("space_")]
    rows = []
    for edit in (1, 2):
        for slot, before in snapshots[(edit, 0)].items():
            marked = snapshots[(edit, 1)][slot]
            after = snapshots[(edit, 2)][slot]
            if before["kind"] != 0:
                continue
            rows.append({
                "edit": edit, "slot": slot, "element": before["element"],
                "events": before["events"], "marked": {field: marked[field] for field in CLEAN},
                "frame_changed_at_marking": [field for field in frame_fields if before[field] != marked[field]],
                "frame_changed_after_update": [field for field in frame_fields if before[field] != after[field]],
                "space_changed_after_update": [field for field in space_fields if before[field] != after[field]],
                "intrinsic_before": {field: before[field] for field in ("intrinsic_known", "min_content", "max_content")},
                "intrinsic_after": {field: after[field] for field in ("intrinsic_known", "min_content", "max_content")},
            })
    return sorted(rows, key=lambda row: (row["edit"], -row["events"], row["slot"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--ordinary", type=Path)
    parser.add_argument("--frames", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--omit-marked", type=Path, help="write a falsifier missing edit1's marked snapshot")
    args = parser.parse_args()
    raw = args.raw.read_text()
    snapshots, ordinary, frames = parse(raw)
    if args.ordinary:
        args.ordinary.write_text(ordinary)
    if args.frames:
        args.frames.write_text(frames)
    if args.summary:
        args.summary.write_text(json.dumps(describe(snapshots), indent=2) + "\n")
    if args.omit_marked:
        kept = []
        for line in raw.splitlines(keepends=True):
            words = line.split()
            if words[:1] == ["flow_probe"] and words[1:3] == ["1", "1"]:
                continue
            kept.append(line)
        args.omit_marked.write_text("".join(kept))
    print(f"flow probe: six complete snapshots, {len(snapshots[(1, 0)])} live contexts, clean before marks, stable post1/before2")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit("flow probe rejected: " + str(error))
