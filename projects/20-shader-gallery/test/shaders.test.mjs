import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SHADERS, wrapFragment, getShader, VERTEX_SRC } from '../src/shaders.js';

test('every shader has a unique id, name, and body', () => {
  const ids = new Set();
  for (const s of SHADERS) {
    assert.ok(s.id && s.name && s.body, `incomplete shader: ${JSON.stringify(s)}`);
    assert.ok(!ids.has(s.id), `duplicate id ${s.id}`);
    ids.add(s.id);
  }
});

test('wrapFragment produces a complete GLSL main() using the snippet', () => {
  const src = wrapFragment(SHADERS[0].body);
  assert.match(src, /precision highp float/);
  assert.match(src, /uniform float time/);
  assert.match(src, /void main\(\)/);
  assert.ok(src.includes(SHADERS[0].body.trim().slice(0, 20)));
});

test('every shader body writes to gl_FragColor', () => {
  for (const s of SHADERS) assert.match(s.body, /gl_FragColor/);
});

test('getShader falls back to the first shader for unknown ids', () => {
  assert.equal(getShader('does-not-exist').id, SHADERS[0].id);
  assert.equal(getShader(SHADERS[1].id).id, SHADERS[1].id);
});

test('vertex shader declares the a_pos attribute', () => {
  assert.match(VERTEX_SRC, /attribute vec2 a_pos/);
});
