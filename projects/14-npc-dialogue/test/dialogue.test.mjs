import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DialogueEngine, buildPersonaPrompt, freeTalk } from '../src/dialogue.js';

const graph = {
  start: 'greet',
  nodes: {
    greet: {
      text: 'Halt! Who goes there?',
      choices: [
        { label: 'A friend.', to: 'friendly', set: { trust: 1 } },
        { label: 'None of your business.', to: 'hostile' },
        { label: 'Show the royal seal.', to: 'vip', requires: { var: 'hasSeal', op: 'has' } },
      ],
    },
    friendly: { text: 'Well met!', choices: [{ label: 'Leave', to: null }] },
    hostile: { text: 'Then begone.', choices: [] },
    vip: { text: 'Right this way, my lord.', choices: [] },
  },
};

test('starts at the start node', () => {
  const d = new DialogueEngine(graph);
  assert.equal(d.node().text, 'Halt! Who goes there?');
});

test('hides choices whose requirements are not met', () => {
  const d = new DialogueEngine(graph); // no seal
  const labels = d.availableChoices().map((c) => c.label);
  assert.ok(!labels.includes('Show the royal seal.'));
  assert.equal(d.availableChoices().length, 2);
});

test('shows gated choice when condition met', () => {
  const d = new DialogueEngine(graph, { hasSeal: true });
  assert.equal(d.availableChoices().length, 3);
});

test('choose advances node and applies side effects', () => {
  const d = new DialogueEngine(graph);
  const next = d.choose(0); // "A friend." sets trust=1
  assert.equal(next.text, 'Well met!');
  assert.equal(d.vars.trust, 1);
});

test('choosing a null target ends the dialogue', () => {
  const d = new DialogueEngine(graph);
  d.choose(0);       // -> friendly
  const end = d.choose(0); // "Leave" -> null
  assert.equal(end, null);
  assert.ok(d.ended());
});

test('a node with no choices is an end state', () => {
  const d = new DialogueEngine(graph, { hasSeal: true });
  d.choose(2); // -> vip (no choices)
  assert.ok(d.ended());
});

test('invalid choice index throws', () => {
  const d = new DialogueEngine(graph);
  assert.throws(() => d.choose(99));
});

test('persona prompt embeds name, facts, and state', () => {
  const npc = { name: 'Borin', role: 'a gruff blacksmith', facts: ['hates elves'], personality: 'grumpy' };
  const p = buildPersonaPrompt(npc, { trust: 2 });
  assert.match(p, /Borin/);
  assert.match(p, /hates elves/);
  assert.match(p, /trust=2/);
});

test('freeTalk sends persona + player line to the LLM', async () => {
  const calls = [];
  const llm = { chat: async (m) => { calls.push(m); return 'Hmph. What do you want?'; } };
  const reply = await freeTalk(llm, { name: 'Borin', role: 'smith' }, {}, 'Hello there');
  assert.equal(reply, 'Hmph. What do you want?');
  assert.equal(calls[0][0].role, 'system');
  assert.equal(calls[0].at(-1).content, 'Hello there');
});
