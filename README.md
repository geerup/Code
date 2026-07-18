# Portfolio Builder

A Claude Code project that turns your infrastructure work into a set of public GitHub
repos for job applications. You review each repo before it's published, then study and
amend it with Claude over time.

## Two files do the work
- **`PROJECTS.md`** — the catalog: every repo, where its source lives, what it contains,
  and which résumé bullet / interview story it backs.
- **`CLAUDE.md`** — the agent's operating manual: the review-gated workflow, the
  no-secrets rule, and the exact `gh`/`git` commands.

## How to run it
1. Put this folder somewhere and `cd` into it.
2. Make sure GitHub CLI is authenticated: `gh auth login` (check with `gh auth status`).
3. Open Claude Code in this folder and give it this first prompt:

   > Read CLAUDE.md and PROJECTS.md, then start Phase 0.

4. Claude checks prerequisites, inventories your existing files, writes `STATUS.md`, and
   stops. Pick a repo (start with `homelab` or `uconsole`).
5. Claude scaffolds it **locally** and stops for your review. When you're happy, say
   "publish homelab" — it creates the repo **private**. Say "make it public" when ready.
6. Come back anytime to amend a repo or run a study/interview session on it.

## The rule that matters
These repos go public. **No secrets ever get committed** — no wallet seeds, RPC
passwords, `.env` values, tailnet addresses, or private keys. The agent scans before
every commit and stops if it finds anything. If in doubt, it treats it as a secret.
