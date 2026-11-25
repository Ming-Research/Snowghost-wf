# Document

How the renderer stores a document: its nodes, the names they carry and their text.

### decision the-document-is-an-arena
A document's nodes live in one `Box<Slots<Node>>` named by `NodeId`, a `u32` index, with parent, child and sibling links held as indices.
- rejected: an agent proposed an owned tree of nodes; the owner rejected it, because tree construction moves and reparents nodes and script holds node identities, which an owned tree cannot express without stored references.

### decision names-are-atoms
Tag, attribute and property names are atoms, `u32` indices into one atom table in which every name the renderer knows has a fixed index generated ahead of time.
- rejected: an agent proposed comparing name bytes or hashes at each use; the owner rejected it, because matching, the cascade and tree construction compare names on every element, and an atom makes each comparison one integer comparison.

### decision document-text-is-utf-8
A document's character data lives in one UTF-8 byte arena per document, named by `u32` spans.
- rejected: an agent proposed UTF-16 document text; the owner rejected it, because only script reads UTF-16, while tokenizing, matching, shaping and line breaking read UTF-8.
