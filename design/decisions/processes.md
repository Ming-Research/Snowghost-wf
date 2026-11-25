# Processes

How Snowghost splits into a renderer in Whitefoot and a shell in Rust, what each owns, and what passes between them.

### decision a-renderer-and-a-shell-joined-by-data
Snowghost is built as a Whitefoot renderer and a Rust shell that exchange data, not calls; main has only the renderer, and neither the shell nor the format between them exists yet.
- rejected: an agent proposed linking the shell's libraries into the renderer as trusted host code; the owner rejected it, because a data boundary keeps those libraries' threading limits out of the renderer, lets each shell part be replaced later, and keeps unproved code in its own process.

### decision the-renderer-parses-page-content
The renderer shapes text, decodes images and checks fonts itself, and is to own the document, style, layout, paint and script.
- rejected: an agent proposed handing page content such as images and fonts to the shell's libraries; the owner rejected it, because the renderer parses the page's untrusted content, which Whitefoot proves memory safe, and that work carries the pipeline's parallel and incremental gains.

### decision the-shell-starts-on-existing-libraries
The shell, not yet written, is to own windows, input, accessibility, rasterization, compositing, presentation, networking and storage, built first on existing libraries such as Skia.
- rejected: an agent proposed writing rasterization and compositing in Whitefoot first; the owner rejected it, because they belong on the GPU, and existing libraries hold years of tuning that would cost too much to rebuild.

### decision the-renderer-sends-facts-the-shell-owns-policy
The renderer is to send the shell facts about the page and never decide how it is drawn; the shell owns every drawing policy, and no policy changes the picture at rest.
- replaced: A renderer that built layer trees for the shell was on main; the owner changed it, because platforms differ in what their compositors and presentation allow, so these choices are measured and changed in the shell without touching the renderer or risking a wrong pixel.
- rejected: an agent proposed holding every frame, animation frames included, to a full redraw's pixels; the owner rejected it, because a large cached subtree under a scaling or rotating animation would then be redrawn every frame, while resampling softens it only until the animation ends.
