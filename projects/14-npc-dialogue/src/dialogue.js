// A reusable NPC dialogue engine: a graph of dialogue nodes with branching
// choices gated by conditions over a shared variable store, plus an optional
// LLM-driven "free talk" mode for open-ended replies. Pure and DOM-free so it's
// unit-testable and embeddable in any game (it feeds the AI Game Master #09).

export class DialogueEngine {
  // graph: { start: nodeId, nodes: { id: { text, choices: [...] } } }
  // choices: { label, to, requires?: {var, op, value}, set?: {var: value} }
  constructor(graph, vars = {}) {
    if (!graph || !graph.nodes || !graph.start) throw new Error('invalid dialogue graph');
    this.graph = graph;
    this.vars = { ...vars };
    this.currentId = graph.start;
    this.history = [];
  }

  node() {
    const n = this.graph.nodes[this.currentId];
    if (!n) throw new Error(`missing node: ${this.currentId}`);
    return n;
  }

  // Choices whose conditions are currently satisfied.
  availableChoices() {
    return (this.node().choices || []).filter((c) => this._meets(c.requires));
  }

  _meets(req) {
    if (!req) return true;
    const actual = this.vars[req.var];
    switch (req.op) {
      case '==': return actual === req.value;
      case '!=': return actual !== req.value;
      case '>': return actual > req.value;
      case '>=': return actual >= req.value;
      case '<': return actual < req.value;
      case '<=': return actual <= req.value;
      case 'has': return Boolean(actual);
      default: throw new Error(`unknown op: ${req.op}`);
    }
  }

  // Pick a choice by index into availableChoices(); applies side effects and
  // advances. Returns the new node (or null if the dialogue ended).
  choose(index) {
    const choices = this.availableChoices();
    const choice = choices[index];
    if (!choice) throw new Error(`no available choice at index ${index}`);
    this.history.push({ node: this.currentId, label: choice.label });
    if (choice.set) for (const [k, v] of Object.entries(choice.set)) this.vars[k] = v;
    if (choice.to == null || !this.graph.nodes[choice.to]) {
      this.currentId = null;
      return null; // conversation ended
    }
    this.currentId = choice.to;
    return this.node();
  }

  ended() {
    return this.currentId === null || (this.node().choices || []).length === 0;
  }
}

// Build a persona system prompt for LLM free-talk, grounded in NPC facts and
// the current variable state so replies stay in character and consistent.
export function buildPersonaPrompt(npc, vars = {}) {
  const facts = (npc.facts || []).map((f) => `- ${f}`).join('\n');
  const state = Object.entries(vars).map(([k, v]) => `${k}=${v}`).join(', ') || 'none';
  return [
    `You are ${npc.name}, ${npc.role}.`,
    npc.personality ? `Personality: ${npc.personality}.` : '',
    facts ? `Known facts:\n${facts}` : '',
    `Current state: ${state}.`,
    'Stay in character. Reply in 1-3 sentences. Never break the fourth wall.',
  ].filter(Boolean).join('\n');
}

// Free-talk turn: ask an injected LLM (any object with chat(messages)->string)
// for an in-character reply. The LLM is mocked in tests.
export async function freeTalk(llm, npc, vars, playerLine, memory = []) {
  const messages = [
    { role: 'system', content: buildPersonaPrompt(npc, vars) },
    ...memory,
    { role: 'user', content: playerLine },
  ];
  return llm.chat(messages);
}
