data=build/research/concurrency
sheets_of() {
	case $1 in
	ecma262) echo "assets/css/ecmarkup.css=$data/ecma262-ecmarkup.css assets/css/print.css=$data/ecma262-print.css" ;;
	html5) echo "" ;;
	apollo11) echo "wikibase.client.init&only=styles&skin=vector-2022=$data/apollo11-modules.css modules=site.styles&only=styles&skin=vector-2022=$data/apollo11-site.css" ;;
	esac
}
