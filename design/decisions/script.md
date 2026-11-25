# Script

How Snowghost is to run a page's JavaScript.

### decision javascript-on-a-whitefoot-interpreter
No script engine is on main yet; JavaScript is to run on an interpreter written in Whitefoot, with no just-in-time compiler.
- rejected: an agent proposed embedding V8, JavaScriptCore or an existing interpreter such as QuickJS; the owner rejected it, because iOS does not let apps make code at run time, a built-in JIT is a security risk, and a renderer that relies on memory safety needs a memory-safe script engine.

### decision the-interpreter-dispatches-by-a-match
The interpreter is to dispatch with an exhaustive match over a closed instruction set, which the Whitefoot compiler lowers to a chain of tail calls.
- rejected: an agent proposed one central dispatch loop; the owner rejected it, because with a chain of tail calls each instruction's handler gets its own branch prediction and register allocation, and a match over a closed sum type is Whitefoot's only dispatch.
