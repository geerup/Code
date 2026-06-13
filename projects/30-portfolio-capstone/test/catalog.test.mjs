import { test } from 'node:test';
import assert from 'node:assert/strict';
import { PROJECTS, THEMES, themeCounts, filterProjects } from '../src/catalog.js';

test('catalog has exactly 30 projects', () => {
  assert.equal(PROJECTS.length, 30);
});

test('project ids are unique and cover 1..30', () => {
  const ids = PROJECTS.map((p) => p.id).sort((a, b) => a - b);
  assert.deepEqual(ids, Array.from({ length: 30 }, (_, i) => i + 1));
});

test('slugs are unique and id-prefixed', () => {
  const slugs = new Set();
  for (const p of PROJECTS) {
    assert.ok(!slugs.has(p.slug), `duplicate slug ${p.slug}`);
    slugs.add(p.slug);
    assert.match(p.slug, new RegExp(`^${String(p.id).padStart(2, '0')}-`), `slug ${p.slug} should start with its id`);
  }
});

test('every project has required fields and a valid theme', () => {
  for (const p of PROJECTS) {
    assert.ok(p.name && p.stack && p.blurb, `incomplete project ${p.id}`);
    assert.ok(THEMES.includes(p.theme), `bad theme ${p.theme} on ${p.id}`);
    assert.ok(['built', 'shipped', 'planned'].includes(p.status));
  }
});

test('there are exactly five flagships', () => {
  assert.equal(PROJECTS.filter((p) => p.flagship).length, 5);
});

test('theme counts sum to 30', () => {
  const counts = themeCounts();
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  assert.equal(total, 30);
});

test('filterProjects narrows by theme and flagship', () => {
  const ai = filterProjects({ theme: 'AI' });
  assert.ok(ai.length > 0 && ai.every((p) => p.theme === 'AI'));
  const flagships = filterProjects({ flagshipOnly: true });
  assert.equal(flagships.length, 5);
});
