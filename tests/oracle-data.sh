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
idna=https://www.unicode.org/Public/17.0.0/idna
css=https://raw.githubusercontent.com/SimonSapin/css-parsing-tests/203ce36bffd617db7f118c551e32794561fb273d
wpt_url=https://raw.githubusercontent.com/web-platform-tests/wpt/b48a5c3fb57854fd217421e247a4f4a0149951a7/url/resources
# PngSuite is served over plain HTTP only; the pinned hash carries its integrity.
pngsuite=http://www.schaik.com/pngsuite/PngSuite-2017jul19.tgz
# html5lib's tree-construction tests now live in WPT.
wpt_parsing=https://raw.githubusercontent.com/web-platform-tests/wpt/b48a5c3fb57854fd217421e247a4f4a0149951a7/html/syntax/parsing/resources
wpt_nodes=https://raw.githubusercontent.com/web-platform-tests/wpt/b48a5c3fb57854fd217421e247a4f4a0149951a7/dom/nodes
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
fetch $wpt_parsing/adoption01.dat wpt-parsing/adoption01.dat b2aba05bd1d832f73a0c6103b3c8b151b283bab7c56887274d81f3a062c4963e
fetch $wpt_parsing/adoption02.dat wpt-parsing/adoption02.dat e091e6976f861ae616fe56c527a78e7247ee7562bcafec996d4e4bda657bd9b7
fetch $wpt_parsing/blocks.dat wpt-parsing/blocks.dat e3b7da1b57a4ec6991443dfc7ab3270f41d0f5959092a49be3e0edca0dae2104
fetch $wpt_parsing/comments01.dat wpt-parsing/comments01.dat c2f3a5ab4baf24f360ee14272aad18c33deffb9a56c2d5964777b1b6e0b8e3c1
fetch $wpt_parsing/doctype01.dat wpt-parsing/doctype01.dat f3a286c09d729eeed9aa63e0aec13ab12336af04590c169543e6d1e1ef4723b2
fetch $wpt_parsing/domjs-unsafe.dat wpt-parsing/domjs-unsafe.dat eef4fb719e027ffaadfb854787d172893850fc561c29efe72d90c5bfa3c8b7ac
fetch $wpt_parsing/entities01.dat wpt-parsing/entities01.dat b73605caac5aed5656184ab8db3f08edff5457ac3186cb04afa28384bca955e3
fetch $wpt_parsing/entities02.dat wpt-parsing/entities02.dat f4e0cd461204b0184709be040c00811b776fbde1a6d002bb1c75d02056d9e54a
fetch $wpt_parsing/foreign-fragment.dat wpt-parsing/foreign-fragment.dat 73e1785753c66420c067e5b29f89b17e7ebe1079687a512040ef19c6d42ac2c2
fetch $wpt_parsing/html5test-com.dat wpt-parsing/html5test-com.dat bc8b465fe4a3ef199142d7f7e8bc6bf7ba10327d3dd795d7abef993bcfb352d0
fetch $wpt_parsing/inbody01.dat wpt-parsing/inbody01.dat cb722f2853ec9613b71ea68e8bb26f474cc450b64612930591ab2656406222fe
fetch $wpt_parsing/isindex.dat wpt-parsing/isindex.dat d152de773e276a07a1cfc91e93f01f3ce52c447c110192f2828dab51be2721b6
fetch $wpt_parsing/main-element.dat wpt-parsing/main-element.dat d56e382994e1a5228ddb2ea49a5ff51ab68487f9a8f79ad34bcad05d40dc1e8f
fetch $wpt_parsing/math.dat wpt-parsing/math.dat 3c2ecc07272c175676ecfafa0cf6e18e74c3293075703702a4b7929fcb0d07bd
fetch $wpt_parsing/menuitem-element.dat wpt-parsing/menuitem-element.dat 08e5e25f38bbc181c840ce5c5203b2566dc03129aeaf105ca2311645d40aae4d
fetch $wpt_parsing/namespace-sensitivity.dat wpt-parsing/namespace-sensitivity.dat 318fbc9926eddf5863524f1503c711ddaea93b55bcbd1eaab71b7e354ddfeb09
fetch $wpt_parsing/noscript01.dat wpt-parsing/noscript01.dat e82449304a6371c14ed490384b6d814b7b1eeb1022dbc5caa2045fc8400655d7
fetch $wpt_parsing/pending-spec-changes-plain-text-unsafe.dat wpt-parsing/pending-spec-changes-plain-text-unsafe.dat f45151f8dc7a4fe1a4b36710cf33606ff43cc98a42f1d2f085a77680683b0c99
fetch $wpt_parsing/pending-spec-changes.dat wpt-parsing/pending-spec-changes.dat a6b7c4ecccabe70de2f24184245e4a73a8d12ed44ee658c3d5d25cce04c9d27f
fetch $wpt_parsing/plain-text-unsafe.dat wpt-parsing/plain-text-unsafe.dat 00fca52972c19a97bb08e18ccd0a7398489e8a7e1929ce75e4004bda70db345b
fetch $wpt_parsing/processing-instructions.dat wpt-parsing/processing-instructions.dat 3d4c6e67b59fda8fa0eb798106a42d244c69a84d7e3a385f9845bfc40071b4f1
fetch $wpt_parsing/quirks01.dat wpt-parsing/quirks01.dat b6717cc15d4ed573ccf6755bc9d52073e675b4d09f23bde07961e27592b9717c
fetch $wpt_parsing/ruby.dat wpt-parsing/ruby.dat 5ae76ac4570d40e6648066798dd3ff729231bec98d3e010fdd67e0257f23a742
fetch $wpt_parsing/scriptdata01.dat wpt-parsing/scriptdata01.dat e32ea3adc3d68c90e62ea50b3a41bf80369d1491958532bf00787b3509667322
fetch $wpt_parsing/scripted_adoption01.dat wpt-parsing/scripted_adoption01.dat 1203be63238a6effc9cc47e3c9b1fa9a0c7e0126a2f78916514afed2d46f42d8
fetch $wpt_parsing/scripted_ark.dat wpt-parsing/scripted_ark.dat 93365261fd9ea7dd9242613b57c23dba94e66bfd837a5d928f725bed81012dd0
fetch $wpt_parsing/scripted_foster01.dat wpt-parsing/scripted_foster01.dat 4bc2c004bfd5efe3ca1b49f3b03de0b31d69347440c97ee1ed83b34ee16ad158
fetch $wpt_parsing/scripted_webkit01.dat wpt-parsing/scripted_webkit01.dat 9d84f68ffd6e8b7b3924c9211280a70a888576b49074654cc9708236834afc58
fetch $wpt_parsing/search-element.dat wpt-parsing/search-element.dat 30be0e9e8cbeea825e0323a7a3a518ab88f44fcada9b4f82b0cc7bbeb9334b76
fetch $wpt_parsing/svg.dat wpt-parsing/svg.dat 4c819b8dbdfbd98cfbce9a535a304b0a16597eb29ccc04077131a62810f309cd
fetch $wpt_parsing/tables01.dat wpt-parsing/tables01.dat bfd4a53246e3acc527c8bb214cc743082e19260e72365001aad3f1d8f4bd08dc
fetch $wpt_parsing/template.dat wpt-parsing/template.dat 24df8f4b1cf98ce3b5313b61cb3baddfcea1f7d3dda99863ceff91bfb751680b
fetch $wpt_parsing/tests1.dat wpt-parsing/tests1.dat aada6e3d12d624051bc978694475bd6a12bcedd7758781ba62425314684d23f3
fetch $wpt_parsing/tests10.dat wpt-parsing/tests10.dat 2d2624a819c323661e396d864ac23440053127b5ea7adb44a5904f5ceee5fa64
fetch $wpt_parsing/tests11.dat wpt-parsing/tests11.dat 276190e2a7b97e8fcf3bd863a4b4b5346b555a8336c00143cb1d0e8956b94a07
fetch $wpt_parsing/tests12.dat wpt-parsing/tests12.dat e6c506cea74979a0d6ca47f6b175c7b6177d6e57db708920a89694e31dfd8a42
fetch $wpt_parsing/tests14.dat wpt-parsing/tests14.dat d151b2426f38de40a5d4ae726e2a56dbc7742a9b1c95299d60c1e2e0fdad1f98
fetch $wpt_parsing/tests15.dat wpt-parsing/tests15.dat ef784ece74cbd760da3a6947aaf4478810246b73c753f25a04be4d11dd806b2d
fetch $wpt_parsing/tests16.dat wpt-parsing/tests16.dat 3350be682713afc1f6dad37059f2551709497a3643c38c26e1fe36fd07d23745
fetch $wpt_parsing/tests17.dat wpt-parsing/tests17.dat 0567680775f58a5b2ad24e234f41d53f68fb2fc3ef7809bebaec0920e2f13c89
fetch $wpt_parsing/tests18.dat wpt-parsing/tests18.dat 5d0019ae43bb4e0b0da9f2e1d57ac0618a607bd8a1324b163ec7a23a1dc120f3
fetch $wpt_parsing/tests19.dat wpt-parsing/tests19.dat a9316b1eb4d2821a18e2c840394c6218bfcdb598857b92631490d9c3c1840ce4
fetch $wpt_parsing/tests2.dat wpt-parsing/tests2.dat 9cf76b5f4890065c04fc82ae828379a55b85cbe76f584fb1ef23dcef0a77b86b
fetch $wpt_parsing/tests20.dat wpt-parsing/tests20.dat 07f7661690c4cd7cc0bbb0f1b9c1e1d65135e07c4dde8bbf106692f687e7d33d
fetch $wpt_parsing/tests21.dat wpt-parsing/tests21.dat b1a67420c79a5131002fefc987084ffb6b6094a3a74b272c6f545a47df06452c
fetch $wpt_parsing/tests22.dat wpt-parsing/tests22.dat 78488328181d0f82f34b1a5e9e456ff7c713b3ff86dab6ace1530f6f07d5370d
fetch $wpt_parsing/tests23.dat wpt-parsing/tests23.dat 2e4752ff4ef898e4a0cf9a450e481440095163d45075a662846a062552afe148
fetch $wpt_parsing/tests24.dat wpt-parsing/tests24.dat fdd5c21f60f42235ded224a03e7182d289088328f460525adaf3c14e772a24ac
fetch $wpt_parsing/tests25.dat wpt-parsing/tests25.dat f2e08fda6d15a08faf9ff0001ec38560d942069cee6b4e264aeedbbacde7da8d
fetch $wpt_parsing/tests26.dat wpt-parsing/tests26.dat d55d24dfca2444fba759d59346cbab21f7e70340dbb14e2c7af8da3d44abd4ab
fetch $wpt_parsing/tests3.dat wpt-parsing/tests3.dat c4b4d8e0ea3d978c49d1e6a985d427164858b71ec980153c4526ed0c398f43b9
fetch $wpt_parsing/tests4.dat wpt-parsing/tests4.dat e6003a52e1cbffc361eca7c739cdd4459074ac8c59766d1eb171b9c9eb42f517
fetch $wpt_parsing/tests5.dat wpt-parsing/tests5.dat bf80b927082290541781844906abdcb72f091488f7a11e8b7d9ac00076dd4fce
fetch $wpt_parsing/tests6.dat wpt-parsing/tests6.dat be16c74d2a9862283262968439c95b9bfce6182ea61055a3c886c28d14f3e01a
fetch $wpt_parsing/tests7.dat wpt-parsing/tests7.dat aeb9569589c809b1a563c0b163173e8cf980a6a4028cb7c210f19c181b56999a
fetch $wpt_parsing/tests8.dat wpt-parsing/tests8.dat f3c8b1baece162e7e8c394540cdf9057266bb738bb0ad539a9d9b2f9d365f162
fetch $wpt_parsing/tests9.dat wpt-parsing/tests9.dat 857820f088506a6d20ea6acefbf19c0a6c4de87a39b24988878066397516b36f
fetch $wpt_parsing/tests_innerHTML_1.dat wpt-parsing/tests_innerHTML_1.dat acb9f835119e302d33204f437d54637a84ae26608ccb7bc961c6f7f44202a44c
fetch $wpt_parsing/tricky01.dat wpt-parsing/tricky01.dat 3fb6d24c5e371860d096ef07f5fff38be3ceaa85f1239bee35cce548b596198a
fetch $wpt_parsing/void-in-phrasing.dat wpt-parsing/void-in-phrasing.dat c8855173aca8ecbd218abc26db34a631393ce0285fffebffdaf69b8bdd6224e9
fetch $wpt_parsing/webkit01.dat wpt-parsing/webkit01.dat 063ca232535a792fa238ae769eeb0ddcc9bd2ee961d3da327ca134612d35d93c
fetch $wpt_parsing/webkit02.dat wpt-parsing/webkit02.dat 03b215350d352faf110df2cc6eac23a44a7f70945b4ea962f0b17bed103459f7
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
fetch $css/stylesheet.json css/stylesheet.json 7292c367370a7ccd4ff47f5c067d692f1ad665340cc7ec4754ea8c3681763794
fetch $css/rule_list.json css/rule_list.json 7a0629ff8747c7837211c2f645a71f32ee69a5ee058ccc4e206d835cd128e55f
fetch $css/declaration_list.json css/declaration_list.json 5d9e4680f64e9a92d9e668d1bc0a69168ab9bb8c6d392de8222b90e9dd88f052
fetch $css/blocks_contents.json css/blocks_contents.json 340c0397813fa100a2a02fb3de2126003a0fe3e678cc9ff9509246e9729efa9c
fetch $css/one_rule.json css/one_rule.json 88f7b1b6049be88e1e2827673b75fc9261986b216e8ee6bf09621fecbe274e3c
fetch $css/one_declaration.json css/one_declaration.json 5360083bfba780c54c2f129080816a87cc68ea0c6ba0de930ba6bbcf85064dd6
fetch $css/An+B.json css/An+B.json 0deb798e84ecf7f08de3c89b3ecdc65caceb8f31a45b03fcf3622e6ba69dfd2b
fetch $wpt_nodes/selectors.js wpt-nodes/selectors.js cffc3f46deb933d63d4cb2cfd811d3ec21ec7804faab4826c8aba1868459e8d1
fetch $wpt_nodes/ParentNode-querySelector-All-content.html wpt-nodes/ParentNode-querySelector-All-content.html 40eff9f6df0986178d2e138c256369fd22f09a8d15ba03fd1bef2ac2c104f9e2
fetch $css/color_function_4.json css/color_function_4.json a28086c67350ddbad70ba432fbdbf603d7c5bd63dce15e06ef0ba5c9e0ffb7c8
fetch $css/color_hexadecimal_3.json css/color_hexadecimal_3.json 0ed46e6f0b465aa50917dcefbafd09bcb89c9f1746f86fba360ee79141bf8e23
fetch $css/color_hexadecimal_4.json css/color_hexadecimal_4.json 8789531747bb83d2b339e79b920b07d3d9bc937b3142fae83f657a00f2b386d9
fetch $css/color_hsl_3.json css/color_hsl_3.json f3967564ee5fe5903126e415240d4b2b5ba90e760e29c3760bbb076a9af4f78b
fetch $css/color_hsl_4.json css/color_hsl_4.json ae13f3b222e2e4c6872163a0a249edff642bb0876aa1a236fa7f1e2774c14a21
fetch $css/color_hwb_4.json css/color_hwb_4.json 7a5b6c531686d1eb678345c2a37306a616eab06d4d60925887ce62e69c1b825a
fetch $css/color_keywords_3.json css/color_keywords_3.json b3a92cdfc563e2bc5cfa5118bd0591672b054eb624a2a30ad27bf1e5e5f27e0d
fetch $css/color_keywords_4.json css/color_keywords_4.json 177b74080543a7b71e46db2038c88069deec7b29f36c56627d71d475723e18e0
fetch $css/color_lab_4.json css/color_lab_4.json f72dc2342f2247b6f8506c601ee65f0754de2e084bfd9ad62fbde2d5f31d8dc1
fetch $css/color_lch_4.json css/color_lch_4.json 568490fdbd7d4d67cf8c075cbb58aca167ee0e0b3365c6ffe2d8c7e4225d9df6
fetch $css/color_oklab_4.json css/color_oklab_4.json beaaa188a8189ec0adffb9ed4959e6910762532b9b2c7998558ede5f37a2eacd
fetch $css/color_oklch_4.json css/color_oklch_4.json 2e575635c6d8fd517430e1e8e84cf20ffb475a4fb095039c9edce8770ee99cd3
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
