# Snowghost

Snowghost is a cross-platform renderer for user interfaces built with web
technology. It implements a chosen subset of the web platform: the part that
mainstream sites and the applications AI coding tools generate actually use.
Its renderer is written in [Whitefoot](https://github.com/mbbill/Whitefoot),
a systems language whose compiler proves memory safety, the absence of data
races and silent overflow, and the independence it uses to run code in
parallel; a shell written in Rust hosts it on each operating system.

The aim is a light platform for web-built applications, with a rendering
pipeline that is parallel and incremental from end to end: a change to one
element reruns only the stages and the parts of the page it affects, and the
independent parts of every stage run on all cores.

## License

MIT; see [LICENSE](LICENSE).
