# ansible-homelab

Idempotent Ansible playbooks that rebuild a small self-hosted homelab from a fresh
Debian install: base OS hardening, Docker Engine, a Tailscale/Headscale overlay client,
and the containerized service stack (Forgejo + act_runner, Vaultwarden, code-server,
Dozzle, Uptime Kuma). It replaces "I click around in my homelab and hope I remember what
I did" with declarative infrastructure-as-code that can be re-applied at any time and
reproduces the same host from bare metal.

**Status: in progress** — roles are written and structured; being validated against the
live Mele N100 host. Only the `.example` inventory and variables are shipped.

## What it provisions

- **base** — timezone, base packages, an admin user with `sudo` + authorized key, SSH
  hardening (no root login, key-only auth), a host-wide tmux config, and
  unattended-upgrades.
- **overlay** — installs the Tailscale client and joins the machine to the overlay using
  a vaulted preauth key. Supports a self-hosted Headscale control plane via extra args.
- **docker** — Docker Engine + the Compose v2 plugin from Docker's official apt repo,
  daemon log rotation, and non-root docker group access.
- **services** — renders and converges the homelab compose stack, every port bound to a
  single configurable address (loopback / overlay interface) so nothing is publicly
  exposed.

## Prerequisites

- A control machine with Ansible installed and SSH access to the target(s).
- Target hosts running Debian (or a Debian derivative) with Python available.
- The Galaxy collections used by the roles:

  ```bash
  ansible-galaxy collection install -r requirements.yml
  ```

## Run

```bash
# 1. Copy the examples and fill in your real values.
cp inventory.example.ini inventory.ini
cp group_vars/all.example.yml group_vars/all.yml

# 2. Vault-encrypt the secrets in group_vars/all.yml (at minimum overlay_auth_key).
ansible-vault encrypt_string 'tskey-REAL-PREAUTH-KEY' --name 'overlay_auth_key'

# 3. Converge everything.
ansible-playbook -i inventory.example.ini site.yml --ask-vault-pass
```

Converge one layer at a time with tags:

```bash
ansible-playbook -i inventory.ini site.yml --tags base,overlay
ansible-playbook -i inventory.ini site.yml --tags docker,services
```

`inventory.example.ini` uses documentation-reserved addresses (`192.0.2.0/24`,
`*.example.internal`) purely so the playbook parses out of the box; point at your own
`inventory.ini` for real runs.

## Roles

| Role     | Purpose                                             | Applies to    | Tag      |
|----------|-----------------------------------------------------|---------------|----------|
| base     | Packages, admin user, SSH hardening, tmux, upgrades | all hosts     | base     |
| overlay  | Tailscale/Headscale client bring-up (vaulted key)   | all hosts     | overlay  |
| docker   | Docker Engine + Compose v2 plugin, log rotation     | `stack` hosts | docker   |
| services | Render + converge the homelab compose stack         | `stack` hosts | services |

## Idempotency notes

Every role converges to a declared end state and reports `changed` only when it actually
changes something, so a second run is a near-total no-op:

- Package/user/file tasks use Ansible's native state modules, which are idempotent by
  design.
- `overlay` gates `tailscale up` behind a `tailscale status` check, so a node that is
  already connected is left alone instead of re-authenticating each run.
- SSH and daemon config changes `notify` handlers, so `sshd`/`docker` restart only when
  their config file actually changes — and `sshd_config` is validated with `sshd -t`
  before it is accepted, so a bad edit fails the task instead of breaking remote access.
- `services` renders the compose file from a template and runs `docker compose up -d`,
  which reconciles running containers against the spec — unchanged containers are not
  touched.

## Design decisions

**Roles over one monolithic playbook.** The stack has four genuinely independent
concerns — OS baseline, overlay networking, container runtime, and the app stack — with
different failure modes and different target groups (`base`/`overlay` run everywhere;
`docker`/`services` only on stack hosts). Splitting them into roles lets me re-run just
one layer with `--tags`, keeps each role's variables and handlers scoped to its own
directory, and makes the whole thing testable a piece at a time. A single long playbook
would couple all of that together and make partial convergence (the normal day-to-day
operation) awkward and risky.

**Only `.example` inventory and vars are shipped.** The real `inventory.ini` and
`group_vars/all.yml` are gitignored on purpose: this repo is public, and those files
carry real hostnames, addresses, and (vault-encrypted) secrets like the overlay preauth
key. Shipping `inventory.example.ini` and `group_vars/all.example.yml` documents the
exact shape a user must fill in without ever leaking topology or key material. Secrets
are vault-encrypted, and the vault password file itself is gitignored and never
committed.

## Repository layout

```
ansible-homelab/
├── README.md
├── LICENSE
├── requirements.yml
├── site.yml
├── inventory.example.ini
├── group_vars/
│   └── all.example.yml
└── roles/
    ├── base/      # packages, users, SSH hardening, tmux
    ├── docker/    # engine + compose plugin
    ├── overlay/   # tailscale/headscale client bring-up
    └── services/  # deploy the homelab compose stack
```
