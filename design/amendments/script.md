Node: script

Decision: JavaScript runs on an interpreter written in Whitefoot with no just-in-time compiler, because iOS does not let ordinary third-party applications generate executable code at run time, an embedded just-in-time compiler is a security risk, and a single-process renderer needs its script engine to be memory safe too, instead of embedding V8 or JavaScriptCore, or an existing interpreter such as QuickJS.

Decision: The interpreter dispatches with an exhaustive match over a closed instruction set that the compiler lowers to a chain of tail calls, because each instruction handler then has its own branch prediction and register allocation and a match over a closed sum type is Whitefoot's only dispatch; this is provisional until Whitefoot provides the lowering and reopens if it cannot, instead of one central dispatch loop.
