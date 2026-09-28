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
idna=https://www.unicode.org/Public/17.0.0/idna
css=https://raw.githubusercontent.com/SimonSapin/css-parsing-tests/203ce36bffd617db7f118c551e32794561fb273d
wpt_url=https://raw.githubusercontent.com/web-platform-tests/wpt/b48a5c3fb57854fd217421e247a4f4a0149951a7/url/resources
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
fetch $ucd/NormalizationTest.txt ucd/NormalizationTest.txt 5019ffd530751a741900c849c0e010332f142a3612234639bd200b82138a87db
fetch $ucd/UnicodeData.txt ucd/UnicodeData.txt 2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c
fetch $ucd/DerivedNormalizationProps.txt ucd/DerivedNormalizationProps.txt 71fd6a206a2c0cdd41feb6b7f656aa31091db45e9cedc926985d718397f9e488
fetch $ucd/extracted/DerivedBidiClass.txt ucd/DerivedBidiClass.txt 4867b4b7f0731ed1bfcd34cc6251211ff1542541fce0734b6fbda139ee80b3a4
fetch $ucd/extracted/DerivedJoiningType.txt ucd/DerivedJoiningType.txt f39ebe974825d6736aee15582250307aa532b2cfab3caf3f86bd23fddc9c5c4d
fetch $idna/IdnaMappingTable.txt idna/IdnaMappingTable.txt 87f05505dc026fdb2bff16132bdc68a8014675836882a9a2b1844540ad3be382
fetch $idna/IdnaTestV2.txt idna/IdnaTestV2.txt beb5d0be20e896189b03209a82fdc34f06351502bbd4b8e2523583fc2954d9cf
fetch $wpt_url/urltestdata.json wpt-url/urltestdata.json 81e85fd3c199c08ef9c34cf651b3580eeedd080316493bfaf277a6b5ff8cf652
fetch $wpt_url/IdnaTestV2.json wpt-url/IdnaTestV2.json 338192b9815dbdace6c035cb1acd50cd737070cd67d6e3f620d2543f63eb0cbb
fetch $wpt_url/toascii.json wpt-url/toascii.json 644eba9d5b593df8095cfa307222f3014542ff9cc02d555f8e5660059d80470f
fetch $css/component_value_list.json css/component_value_list.json a8d7a5252373b892cfcac359360930ad9a57ed918a84331bcf0c872b80f83200
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
