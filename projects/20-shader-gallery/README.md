# ✨ Shader Gallery (#20)

A small WebGL gallery of animated GLSL fragment shaders rendered on a full-screen
quad. Plasma, ripple rings, and animated cell (Voronoi) noise — switch live.

**Live demo:** static site (deploy `index.html` to Vercel).

## How it works
- One vertex shader draws a fullscreen triangle strip; each gallery entry is a
  **fragment-shader snippet** (`src/shaders.js`) that colors every pixel from
  `uv`, `time`, and `res` uniforms.
- `wrapFragment` assembles a complete GLSL program from a snippet, so the gallery
  and the unit tests share exactly one source of truth.

## Run
```bash
npm test          # validates shader registry + GLSL assembly (node --test)
npm run serve     # http://localhost:8082
```

GPU compilation can't run in CI, so tests cover the shared, host-side logic
(registry integrity, fragment assembly, fallback selection).

## What I learned / next
- Fragment-shader fundamentals: distance fields, hash noise, animation via a
  time uniform.
- Next: a code editor panel with live recompile + error reporting, and saving
  shaders to shareable URLs.
