# CLAUDE.md — Portfolio Builder Agent Instructions

You are operating inside a Claude Code project whose job is to turn a list of real
infrastructure work into a set of public GitHub repositories that function as a
job-search portfolio for roles in NOC / Linux sysadmin / DevOps / SOC / datacenter.

The catalog of what to build lives in **`PROJECTS.md`**. That file is the source of
truth. This file (`CLAUDE.md`) tells you *how* to work.

---

## THE ONE RULE THAT OVERRIDES EVERYTHING: NO SECRETS LEAVE THE MACHINE

These repos will be **public**. This portfolio touches crypto self-custody, VPN
overlays, and self-hosted secrets managers. A single committed secret is
unrecoverable once pushed.

**Never stage, commit, or push:**
- Wallet material of any kind: seed phrases, mnemonics, `wallet.dat`, Monero wallet
  keys/`.keys` files, xpub/xprv, WIF private keys, PSBTs with real data, hardware
  wallet derivation output.
- RPC credentials (bitcoin.conf `rpcpassword`, monerod rpc-login), Vaultwarden data,
  `.env` files with real values, API tokens, SSH private keys, TLS private keys.
- Tailnet identifiers: `100.x.y.z` CGNAT addresses, MagicDNS names, tailnet name,
  Headscale preauth keys, node keys.
- LAN topology that deanonymizes the operator: public IPs, real router/LAN subnets if
  the operator wants them private, MAC addresses, WAN hostnames.

Before **every** `git add`/commit and before **every** push, run the sanitization scan
(see below). If the scan flags anything, STOP and show the operator — do not proceed on
your own judgment.

If you are ever unsure whether something is a secret: treat it as one.

---

## HOW TO USE THIS PROJECT (first message the operator gives you)

The operator's opening prompt will be something like:
> "Read CLAUDE.md and PROJECTS.md, then start Phase 0."

On that prompt: read both files fully, run the prerequisite check, run inventory, write
`STATUS.md`, and then **stop and report** — do not start scaffolding repos until the
operator picks one.

---

## PREREQUISITE CHECK (Phase 0, step 1)

Run and report results. Do not assume — verify.

```bash
gh auth status              # must be logged in; note the account/owner
gh --version
git --version
git config user.name; git config user.email   # commits will carry these
```

If `gh` is not authenticated, tell the operator to run `gh auth login` and stop.
If `git config user.email` is a personal address the operator doesn't want public, flag
it — commits are public on public repos.

---

## SOURCE OF TRUTH & OWNER

- **`PROJECTS.md`** defines every repo: name, status, description, target roles, where
  the existing source files live, required structure, and the linked résumé bullets and
  interview story for study.
- The GitHub **owner** (personal account vs. the `san-media-tech` org) is a variable the
  operator sets. Ask once in Phase 0, store it in `STATUS.md`, reuse it. Do not hardcode.
- Repos are created **private** and only flipped **public** on the operator's explicit
  instruction after review.

---

## WORKFLOW — FOUR PHASES, LOCAL-FIRST, HUMAN-GATED

The operator explicitly wants to **review each repo before it becomes a GitHub project**,
then **study and amend it with you over time**. So: you scaffold locally, they review,
you publish on command, they iterate. Never `gh repo create` before review.

### Phase 0 — Inventory
1. Prerequisite check (above).
2. Read `PROJECTS.md` fully.
3. Locate existing source material. For each PUBLISH repo, `PROJECTS.md` lists a probable
   source path. Confirm what actually exists:
   ```bash
   ls -la ~/Desktop/uConsole_Setup_Reference.txt 2>/dev/null
   ls -la /mnt/user-data/outputs/*.md 2>/dev/null
   # ask the operator for paths to: guide.html, the Mele compose files, .bashrc, tmux.conf
   ```
   If a path is missing, ask the operator — do not fabricate file contents.
4. Write `STATUS.md` (format below) listing all repos with state `not-started`.
5. **Stop.** Report inventory and ask which repo to start with. Suggest the priority
   order from `PROJECTS.md` (start with `homelab` or `uconsole` — highest signal, source
   already exists).

### Phase 1 — Scaffold ONE repo locally
Work on a single repo unless told otherwise. For the chosen repo:
1. Create `repos/<name>/` in this project directory. This is a staging area, not the
   final repo yet.
2. **Import** existing files (copy from the source path) or **generate** structure per
   the repo's spec in `PROJECTS.md`.
3. Sanitize every imported file (scan + manual review). Replace real secrets with
   placeholders and create a matching `.env.example`.
4. Write the standard repo files (see "Repo scaffold standard").
5. Write the README from the sections listed in that repo's `PROJECTS.md` entry. Preserve
   the **status label** honestly — if the work is `planned`/`evaluated`, the README says
   so; do not describe planned work as running.
6. Run the sanitization scan one more time across the whole `repos/<name>/` tree.
7. Present a file tree and the README to the operator. **Stop for review.**

### Phase 2 — Review gate → publish
Only when the operator says something like "publish `<name>`":
```bash
cd repos/<name>
git init -b main
git add -A
# FINAL sanitization scan here, on staged content:
git diff --cached | rg -i 'BEGIN.*PRIVATE KEY|rpcpassword|mnemonic|seed|xprv|100\.[0-9]' && echo "!!! REVIEW BEFORE COMMIT" || echo "scan clean"
git commit -m "Initial import: <one-line description>"
gh repo create <owner>/<name> --private --source=. --remote=origin --push
```
Report the repo URL. Keep it **private**. Only run
`gh repo edit <owner>/<name> --visibility public --accept-visibility-change-consequences`
when the operator explicitly says to make it public.
Update `STATUS.md` → `published-private` (or `public`).

### Phase 3 — Study & iterate loop
This is the ongoing mode after a repo exists. When the operator returns to a repo:
- **Amend:** make the specific edits requested, commit with a clear message, push.
- **Study:** on request, act as an interviewer. Use the linked résumé bullets and the
  interview story in `PROJECTS.md` for that repo. Ask the operator to explain the repo's
  key decision (e.g. "why SD-first boot order with NVMe fallback?", "why does
  `--socks5-hostname` matter?"). Fill gaps in the README from their answers. The goal is
  that the operator can defend every line of every repo in an interview.
- Keep `STATUS.md` current after every session.

---

## REPO SCAFFOLD STANDARD (every repo gets these)

```
<name>/
├── README.md            # from the sections in PROJECTS.md for this repo
├── LICENSE              # MIT unless operator says otherwise
├── .gitignore           # language/tool appropriate + secret patterns below
├── .env.example         # if the project uses env/secrets — placeholders only
└── docs/                # optional: diagrams, longer writeups, screenshots
```

Baseline `.gitignore` additions for **every** repo (append to tool-specific ignores):
```
.env
.env.*
!.env.example
*.key
*.pem
*_rsa
*_ed25519
id_*
*.wallet
wallet.dat
*.keys
bitcoin.conf
monerod.conf
secrets/
```

README quality bar (non-negotiable for portfolio value):
- First paragraph: what this is and the problem it solves. No preamble.
- A status line near the top: `Status: running | evaluated | planned` — honest.
- At least one **decision + rationale** ("why this way, not the obvious way"). This is
  what interviewers read.
- Real commands/config the reader could run, not vague description.
- If planned/blocked, a short "current state / next step" so it doesn't read as vaporware.

---

## SANITIZATION SCAN (run before every commit and push)

`rg` (ripgrep) is preferred; fall back to `grep -rEi`.

```bash
# From inside the repo staging dir. Review EVERY hit by hand.
rg -i --hidden -n \
  -e 'BEGIN [A-Z ]*PRIVATE KEY' \
  -e 'rpcpassword|rpcuser' \
  -e 'rpc-login' \
  -e 'mnemonic|seed phrase|seed_words|passphrase' \
  -e 'xprv|xpub|zprv|[5KL][1-9A-HJ-NP-Za-km-z]{50,}' \
  -e '\b100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]+\.[0-9]+\b' \
  -e '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}' \
  -e 'AKIA[0-9A-Z]{16}|ghp_[0-9A-Za-z]{36}|sk-[0-9A-Za-z]{20,}' \
  -e 'tskey-|nodekey:|authkey' \
  . && echo ">>> HITS ABOVE — do not commit until each is cleared" \
    || echo "scan clean"
```

Patterns cover: private keys, Bitcoin/Monero RPC creds and wallet material, Base58 keys,
Tailscale CGNAT range + auth/node keys, MAC addresses, common cloud/API/GitHub tokens.
The scan is a net, not a guarantee — also eyeball anything that looks like a real host,
address, or credential.

---

## STATUS.md FORMAT (you create and maintain this)

```markdown
# Portfolio Build Status
Owner: <github-owner>        Updated: <date>

| Repo              | Status            | Source        | Notes                    |
|-------------------|-------------------|---------------|--------------------------|
| homelab           | published-private | Mele compose  | needs arch diagram       |
| uconsole          | scaffolding       | ~/Desktop txt | importing power table    |
| ...               | not-started       | -             | -                        |

States: not-started → scaffolding → in-review → published-private → public
```

---

## GUARDRAILS / DON'TS

- Don't create any remote repo before the operator reviews the local scaffold.
- Don't make anything public without an explicit "make it public."
- Don't invent file contents, config, or results the operator didn't produce. If a repo
  is `planned`, scaffold the README and structure and label it planned — don't fake logs,
  screenshots, or metrics.
- Don't inflate status. A repo describing evaluated-but-not-deployed work must say so.
- Don't batch-create all repos at once. One at a time, review-gated, unless told.
- Don't commit large binaries (full-Wikipedia ZIMs, pcaps over ~a few MB, blockchain
  data). Reference them; commit small representative samples only.
- Don't rewrite the operator's voice into marketing. Keep it technical and plain.
