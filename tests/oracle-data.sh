#!/bin/sh
# Fetches the pinned oracle data of the renderer's leaf modules into DIR
# (the agent writer trial and later leaves), checks every file's SHA-256,
# and derives the PNG references with the libpng program REFERENCE.
#
#   tests/oracle-data.sh DIR REFERENCE
set -eu

dir=$1
reference=$2
ucd=https://www.unicode.org/Public/17.0.0/ucd
css=https://raw.githubusercontent.com/SimonSapin/css-parsing-tests/203ce36bffd617db7f118c551e32794561fb273d
# PngSuite is served over plain HTTP only; the pinned hash carries its integrity.
pngsuite=http://www.schaik.com/pngsuite/PngSuite-2017jul19.tgz
html5lib=https://raw.githubusercontent.com/html5lib/html5lib-tests/224991ec10db04f056a89eed8b0bd8695fd2950e
# The HTML standard's named character references; the file is unversioned,
# so its hash pins the copy the tokenizer was written against.
entities=https://html.spec.whatwg.org/entities.json

fetch() { # URL FILE SHA256
    if [ -f "$dir/$2" ] && echo "$3  $dir/$2" | sha256sum -c --status; then
        return
    fi
    mkdir -p "$(dirname "$dir/$2")"
    curl -fsSL --retry 3 -o "$dir/$2.part" "$1"
    if ! echo "$3  $dir/$2.part" | sha256sum -c --status; then
        echo "oracle-data: $1 does not match its pinned SHA-256" >&2
        exit 1
    fi
    mv "$dir/$2.part" "$dir/$2"
}

fetch $ucd/LineBreak.txt ucd/LineBreak.txt e6a18fa91f8f6a6f8e534b1d3f128c21ada45bfe152eb6b1bcc5e15fd8ac92e6
fetch $ucd/EastAsianWidth.txt ucd/EastAsianWidth.txt ea7ce50f3444a050333448dffef1cadd9325af55cbb764b4a2280faf52170a33
fetch $ucd/extracted/DerivedGeneralCategory.txt ucd/DerivedGeneralCategory.txt d62e5bab70ca74f099343f71224fa051cb1fdd61a1ab45c0488c44cfc0b6102e
fetch $ucd/emoji/emoji-data.txt ucd/emoji-data.txt 2cb2bb9455cda83e8481541ecf5b6dfda66a3bb89efa3fa7c5297eccf607b72b
fetch $ucd/auxiliary/LineBreakTest.txt ucd/LineBreakTest.txt e69884e0dde6a8724873f885d68c52dc14518abf9ae4ca9e2283b8773db3b752
fetch $css/component_value_list.json css/component_value_list.json a8d7a5252373b892cfcac359360930ad9a57ed918a84331bcf0c872b80f83200
fetch $html5lib/tokenizer/contentModelFlags.test html5lib/contentModelFlags.test 77784a505a528950761cfb3c76617afade28b27c3be2a8c37dce3c3d8988391d
fetch $html5lib/tokenizer/domjs.test html5lib/domjs.test 3273e7861bbdb094571e4b0813ffdd934fe2bfd65864600fef62e8e3b807131a
fetch $html5lib/tokenizer/entities.test html5lib/entities.test fe17483810a00247579f5f129ca9c007fbab6755ba839523e29aa9f8875f4085
fetch $html5lib/tokenizer/escapeFlag.test html5lib/escapeFlag.test edbd2e070a14fc67f6bbc104e50207f0fe206a21891c260deea3d227b32c93c9
fetch $html5lib/tokenizer/namedEntities.test html5lib/namedEntities.test a7f0e59ff7653820330548776cb3031c18e45f5fd1481a9813d9c7acee89bd6e
fetch $html5lib/tokenizer/numericEntities.test html5lib/numericEntities.test 679296c976252322ece27e2b113a5358a0aa3b0b8ecd2d6d9b365f9d1b0f9632
fetch $html5lib/tokenizer/pendingSpecChanges.test html5lib/pendingSpecChanges.test 6b56d81ca09afa47d8cb0f33e3fb7169010c3a64493e608ebec921ac098ff8e9
fetch $html5lib/tokenizer/test1.test html5lib/test1.test 524fcfa4d561a14f0c4e72e0573549abe6341fd4dfb8e16bc2dcf59a608a7219
fetch $html5lib/tokenizer/test2.test html5lib/test2.test f6450e77760cea823258de86f8e08894a1815671dbec0d74e7fbdab075596e37
fetch $html5lib/tokenizer/test3.test html5lib/test3.test 9912fa27f03344243f1baa96d9690a5c2a4a9c9426c70da5cbf5c62391d62de4
fetch $html5lib/tokenizer/test4.test html5lib/test4.test c4967118aecbf8eb2ca34d5c5306f536614acca03e58610f75fbd9efa89fbb42
fetch $html5lib/tokenizer/unicodeChars.test html5lib/unicodeChars.test 22b7263a840da38179b13693bbfe72f0507dcd41951622456a0d3f5300ba42bd
fetch $html5lib/tokenizer/unicodeCharsProblematic.test html5lib/unicodeCharsProblematic.test 3c166d5cfa24ee60fd7310ff0f5057e4ae0c649842ec446b5949215759e19a68
fetch $entities html/entities.json d741d877ac77c4194c4ad526b5b4a19aef8dfe411ab840a466891cdbb9f362e6
fetch $pngsuite PngSuite-2017jul19.tgz 0294b244c95a8342c01b00010cf34abdcabc7c6a34fd0fe1bd963917537bfdc8

# PngSuite: every image with its libpng reference, and the case list
# ("valid NAME" or "invalid NAME") the driver reads. Names starting with x
# are the suite's corrupted files, which both decoders must reject.
rm -rf "$dir/pngsuite"
mkdir -p "$dir/pngsuite"
tar -xzf "$dir/PngSuite-2017jul19.tgz" -C "$dir/pngsuite"
: > "$dir/pngsuite/cases.txt"
for png in "$dir"/pngsuite/*.png; do
    name=$(basename "$png" .png)
    if "$reference" decode "$png" "$dir/pngsuite/$name.rgba"; then
        case $name in
            x*) echo "oracle-data: libpng accepts corrupted $name" >&2; exit 1 ;;
        esac
        echo "valid $name" >> "$dir/pngsuite/cases.txt"
    else
        case $name in
            x*) echo "invalid $name" >> "$dir/pngsuite/cases.txt" ;;
            *) echo "oracle-data: libpng rejects $name" >&2; exit 1 ;;
        esac
    fi
done

rm -rf "$dir/png-speed"
mkdir -p "$dir/png-speed"
"$reference" generate "$dir/png-speed"
