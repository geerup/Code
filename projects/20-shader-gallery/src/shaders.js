// Fragment-shader snippets for a full-screen quad. Each exposes a `mainImage`
// body operating on `uv` (0..1), `time`, and `res`. `wrapFragment` assembles a
// complete GLSL ES 1.00 fragment shader so the gallery (and tests) share one
// source of truth.

export const SHADERS = [
  {
    id: 'plasma',
    name: 'Plasma',
    body: `
      float v = sin(uv.x * 10.0 + time);
      v += sin((uv.y * 10.0 + time) * 0.5);
      v += sin((uv.x + uv.y) * 10.0 + time);
      vec3 col = vec3(sin(v * 3.1415), sin(v * 3.1415 + 2.0), sin(v * 3.1415 + 4.0));
      gl_FragColor = vec4(col * 0.5 + 0.5, 1.0);`,
  },
  {
    id: 'rings',
    name: 'Ripple Rings',
    body: `
      vec2 p = uv - 0.5;
      p.x *= res.x / res.y;
      float d = length(p);
      float r = sin(d * 40.0 - time * 3.0) * 0.5 + 0.5;
      vec3 col = mix(vec3(0.02, 0.1, 0.2), vec3(0.4, 0.9, 1.0), r);
      gl_FragColor = vec4(col, 1.0);`,
  },
  {
    id: 'voronoi',
    name: 'Cell Noise',
    body: `
      vec2 p = uv * 8.0;
      vec2 i = floor(p);
      float md = 1.0;
      for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
          vec2 g = vec2(float(x), float(y));
          vec2 o = fract(sin(vec2(dot(i + g, vec2(127.1, 311.7)),
                                  dot(i + g, vec2(269.5, 183.3)))) * 43758.5453);
          o = 0.5 + 0.5 * sin(time + 6.2831 * o);
          float d = length(g + o - fract(p));
          md = min(md, d);
        }
      }
      gl_FragColor = vec4(vec3(md * md, md, 0.6), 1.0);`,
  },
];

export const VERTEX_SRC = `
attribute vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }`;

// Build a complete fragment shader from a snippet body.
export function wrapFragment(body) {
  return `
precision highp float;
uniform float time;
uniform vec2 res;
void main() {
  vec2 uv = gl_FragCoord.xy / res;
  ${body}
}`;
}

export function getShader(id) {
  return SHADERS.find((s) => s.id === id) || SHADERS[0];
}
