#!/bin/sh
# Fetches the pinned oracle data for the agent writer trial into DIR
# (research/investigations/agent-writer-trial), checks every file's SHA-256,
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
fetch $css/stylesheet.json css/stylesheet.json 7292c367370a7ccd4ff47f5c067d692f1ad665340cc7ec4754ea8c3681763794
fetch $css/rule_list.json css/rule_list.json 7a0629ff8747c7837211c2f645a71f32ee69a5ee058ccc4e206d835cd128e55f
fetch $css/declaration_list.json css/declaration_list.json 5d9e4680f64e9a92d9e668d1bc0a69168ab9bb8c6d392de8222b90e9dd88f052
fetch $css/blocks_contents.json css/blocks_contents.json 340c0397813fa100a2a02fb3de2126003a0fe3e678cc9ff9509246e9729efa9c
fetch $css/one_rule.json css/one_rule.json 88f7b1b6049be88e1e2827673b75fc9261986b216e8ee6bf09621fecbe274e3c
fetch $css/one_declaration.json css/one_declaration.json 5360083bfba780c54c2f129080816a87cc68ea0c6ba0de930ba6bbcf85064dd6
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
