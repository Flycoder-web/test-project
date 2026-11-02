# Grape Contributing Guide

> Language: **English** (current) · [中文](CONTRIBUTING.zh.md)

> Grape — AI Native DevOps: turning any Git project into an autonomous, "AI-driven, human-gated" development workflow.
> This document defines collaboration, branching, release and quality standards. **Read it before you submit — five minutes is enough to get going.**

Quick navigation

| What you want to do | Where to look |
|---------------------|---------------|
| Your first contribution (newcomer) | [Newcomer path](#16-newcomer-path-good-first-issue) |
| Report a bug / suggest an idea | [Issues — discuss first](#3-issues--discuss-first) |
| Start writing code | [Branch model](#2-branch-model) → [Contribution flow](#4-contribution-flow-from-issue-to-merge) |
| How to write commit messages | [Commit message convention](#5-commit-message-convention) |
| How to run the tests | [Quality requirements](#7-code-quality-requirements) |
| Make it into Friday's release | [Friday release flow](#9-friday-release-and-tagging) |
| Urgent defect | [Hotfix channel](#10-emergency-hotfix-channel) |
| I don't write code | [Contributing without code](#174-contributing-without-writing-code) |

---

## 1. Workflow overview

```
main (trunk) ──────────────────────────▶ always releasable, only accepts release merges
   │                             ▲              ▲
   │ branch off every Monday     │ merged back  │ merged back
   ▼                             │ (MR + no-ff) │ (MR + no-ff)
 weekly-01 ────────────────▶ weekly-02 ───────▶ ...
   │  ▲                         │  ▲
   │  │ MR merges (feat/fix)    │  │
   ▼  │                         ▼  │
 feat/xxx  fix/xxx  docs/xxx  refactor/xxx   chore/xxx
   (branched off the weekly target, one task per branch)
   │
   ───────────────── hotfix/xxx (urgent: targets main + current weekly)
```

- **Each iteration ships one weekly version**; the test environment rolls forward with the weekly branch.
- Features never go straight into `main`: they land in the current `weekly-xx` first, then get merged back into `main` and tagged on Friday.
- Conflicts, reviews and release volume are all concentrated into "once a week" — a stable team rhythm that still works for open collaboration.

## 2. Branch model

### 2.1 Branches at a glance

| Branch | Naming | Lifetime | Who merges | Purpose |
|--------|--------|----------|------------|---------|
| Trunk | `main` | Permanent | Maintainers | The only publicly releasable branch, always stable; receives the weekly merge on Friday |
| Weekly iteration | `weekly-01`, `weekly-02`… | One week | Maintainers | Collection point for the iteration's features; deployment source for the test environment |
| Feature | `feat/xxx` | Short (≤ 1 week) | Created by contributors | New functionality, branched off the current weekly |
| Fix | `fix/xxx` | Short | Created by contributors | Defect fixes |
| Refactor | `refactor/xxx` | Short | Created by contributors | No behaviour change |
| Docs | `docs/xxx` | Short | Created by contributors | Documentation, examples |
| Chore | `chore/xxx` | Short | Created by contributors | Build, toolchain, dependencies |
| Hotfix | `hotfix/xxx` | Very short | Maintainers | Critical production/test defects, no waiting for Friday |

### 2.2 Core rules

- **Feature branches come off the current `weekly-xx`**, and **the merge request targets `weekly-x`** (not `main`); maintainers merge it back into `main` on Friday. Fewer conflicts, cleaner review, a controllable merge-back.
- **`main` and `weekly-xx` are protected**: direct pushes are not allowed — merge request + review + green CI is required (see [Permissions and protection](#112-permissions-and-protections)).
- **Keep branches small**: one issue / one responsibility per branch, mergeable within a week; do not start stuffing large features in after Monday.
- Branch names use `prefix/short-description` (lowercase kebab-case), e.g. `feat/issue-37-repo-template`.

### 2.3 Weekly iteration timeline (recommended, may float)

| When | Action |
|------|--------|
| Monday 09:30 | Branch `weekly-0X` off the latest `main` HEAD (X = week number, e.g. `weekly-01`); push a placeholder/empty commit or the first merge point |
| Monday–Thursday | Contributor feature MRs → `weekly-0X`; every push triggers CI plus an automatic test-environment deployment and verification |
| Friday FREEZE point (e.g. 15:00) | The current weekly freezes: only approved fixes and hotfixes; no new features |
| Friday | Merge `weekly-0X` → `main` (via MR), tag (`weekly-0X` + semver), generate the changelog, publish release notes |
| Next Monday | Branch `weekly-0(X+1)` off the new main; the `weekly-0X` branch can be archived (its tag is kept forever) |

## 3. Issues — discuss first

**Open an issue and agree on the direction before writing code**, so the work isn't wasted.

- **Bug report**: state the environment (OS / Python version), reproduction steps, expected vs actual behaviour, and the relevant logs.
- **Feature request**: describe the use case, the expected behaviour and, optionally, an implementation sketch. Try to pin it to a specific Skill / Agent / module.
- Suggested labels: `bug`, `feature`, `good-first-issue`, `help-wanted`, `p3` (low), `p2`, `p1` (high).
- Claim the issue or leave a comment before you start, so nobody duplicates your work.

## 4. Contribution flow (from issue to merge)

```
Issue confirmed → claim → branch off the current weekly → create feature branch → develop + commit
   → test locally → push → open MR against weekly-0X → review (human + QA Agent) → CI green → merged → merged back on Friday
```

1. **Branch off `weekly-0X`**:
   ```bash
   git checkout weekly-01
   git pull origin weekly-01
   git checkout -b feat/issue-37-repo-template
   ```
2. **Develop + commit** (convention in [§5]).
3. **Run the local quality checks** (commands in [§7]) and make sure everything passes.
4. **Push and open an MR** with **the current `weekly-0X`** as the target branch, using the [§6] template: what changed, why, how it was tested, and the linked issue number.
5. **Wait for review**:
   - A project owner (the owner listed in `MAINTAINER`, currently `@Jason7602`) or a maintainer approves;
   - Grape's own **QA Agent assists the review** (runs tests and static checks automatically) — it is an assistant, not a replacement for human judgement;
   - If changes are requested, keep committing on the **same branch**; **do not modify the original MR after it has been merged**.
6. **Green CI + approved review** → a maintainer squashes/merges it into `weekly-0X`.
7. After the merge, the test environment deploys that weekly branch automatically — **contributors are encouraged to self-test there** (checklist in [§8]).

> The only difference between collaborators and outside contributors is "branch vs fork": outside contributors fork, then open the MR from `your-username/fork-branch` → `weekly-0X`. The flow is identical.

## 5. Commit message convention

**Commit messages are written in English**, following **Conventional Commits** and referencing the issue:

```
<type>(<scope>): <subject>

<body explaining what / why>
```

- type: `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`, `perf`, `security`.
- scope is optional (module/backend); the subject is all lowercase, concise, starting with a verb.
- **Reference the issue** (recommended): `fix(issue-37): fix template auth`.
- One commit does one thing; no "while I'm here" changes.

```bash
# example
git commit -s -m "feat(skill): add xxx skill description

Closes #37"
```

- **DCO sign-off**: every commit ends with `Signed-off-by`:
  ```
  Signed-off-by: Your Name <your.email@example.com>
  ```
  (`git commit -s` adds it automatically; see [§17] for what it means.)

Good / bad examples:

``` 
# good
feat(skill): add xxx skill description
fix(issue-37): fix template auth bug
docs: add bilingual README
```
```bash
# bad
# "update stuff", one huge commit mixing UI+DB+docs, no issue reference, no description
# non-English commit message
```

## 6. MR description template

```markdown
## Linked issue
Closes #37

## What changed
- Brief description…

## Testing
- [ ] Local pytest fully green (commands in §7)
- [ ] New/changed code is covered
- [ ] Verified in the test environment (after the weekly branch was deployed)

## Impact / risk
- Skills / Agents / configuration involved…
```

## 7. Code quality requirements

| Item | Requirement |
|------|-------------|
| Unit tests | New/changed code must ship with tests |
| Test command | `python -m pytest tests/ -v` (skips `e2e_ui` by default for determinism; run the `e2e_ui` scenarios with `python -m pytest tests/ -m e2e_ui`) |
| Coverage | `python -m pytest tests/ --cov`; the current gate is **line coverage ≥ 70%** (`.coveragerc` `fail_under=70`, to be raised once stable) |
| Code style | Match the surrounding code; no unused dependencies; never commit secrets (tokens/credentials belong in `.env` or config files, which are gitignored) |
| Security | Do not weaken authentication/authorization; never concatenate external input into SQL or shell commands (mind the permissions on `.env.example` and `configs`) |

CI runs automatically on every MR push: lint + unit tests + coverage gate + build.

## 8. Test environment (weekly branches)

- Every push to `weekly-0X` triggers an automatic build and deployment to the test environment.
- The test environment tracks only that week's `weekly-0X`, **never feature branches**, so what you test is exactly the set that will be released.
- Verification checklist (regression):
  - [ ] The multi-agent pipeline runs end to end (VOD→Issue→Coding→QA→SRE)
  - [ ] The key paths of all three entry points (GitCode Webhook / Feishu / WebUI)
  - [ ] End-to-end scenarios for the features added in this version
  - [ ] Impact of data migrations / configuration changes (if any)

## 9. Friday release and tagging

Friday is the release window for the current weekly, executed by a maintainer or the release duty owner:

1. **FREEZE**: `weekly-0X` freezes; no new features (only approved fixes and hotfixes).
2. **Merge back into the trunk**: merge `weekly-0X` into `main`. A **merge commit (`--no-ff`) is recommended**, noting `weekly-0X → main` and the MR number so the release history stays traceable; CI runs once more on `main` afterwards (regression gate).
3. **Tag** (so the tag matches what was merged into `main`):
   ```bash
   git checkout weekly-01
   git tag weekly-01                  # weekly version number, same content as the main merge result
   git tag -a v0.4.0 -m "weekly-01 release"   # recommended: also tag a semantic version for external references
   git push origin weekly-01 --tags
   ```
   - `weekly-0X` is the internal release number; **point a SemVer `vX.Y.Z` tag at the same commit for public use** (production and third parties should rely on SemVer).
4. **Release artifacts**: generate the changelog with Grape's `changelog-gen` Skill (or by hand); write release notes; link the issues folded into this iteration.
5. **Archive**: archive that week's branch (`git branch -d weekly-01`) and keep the tag forever; **never delete a tag**.

## 10. Emergency hotfix channel

Critical defects (testing blocked / production risk) **do not wait for Friday**:

```
main ──────────────────── ... 
   └             └
   └ hotfix/xxx  (branched off main)
   └  → fix → MR targets main directly (+ the current weekly-0X in parallel, so the test environment stays aligned)
   └  → CI green → merge immediately → patch tag (e.g. v0.4.1)
```

1. Branch `hotfix/xxx` off `main` and open the MR **against `main`**.
2. **Also cherry-pick it into the current `weekly-0X`** (or open a small second MR) so the test environment gets the fix too.
3. Tag the patch version (`v0.4.1`) right after merging into main — don't drag it to Friday.

## 11. Permissions, protection and automation

### 11.1 Default responsibilities

| Owner | Responsibilities |
|-------|------------------|
| Maintainer (owner, see MAINTAINER) | Review/merge MRs, weekly merge-back, tagging, releases, branch protection |
| Contributor | Feature/fix development, self-testing in the test environment |
| QA Agent (Grape) | Automatic assistance on every MR: tests, static checks, security scanning |

### 11.2 Permissions and protections

- `main`, `weekly-0X`: **direct pushes forbidden**; a review (≥ 1 approval, the module owner among MAINTAINER may finalize) and green CI are required before a maintainer merges.
- `feat/*`, `fix/*` etc.: contributors own them, but merges always go through an MR.
- Force-push and deletion of `main`/`weekly` branches are disabled platform-wide.

### 11.3 Recommended automation

- CI: MR push triggers lint + unit tests + coverage + build; a `weekly-0X` push additionally deploys the test environment.
- Dependency-update bot (if wanted): disable auto-merge; review DCO/semantics by hand before merging, so failures don't spike mid-week.
- Tagging / releases: CI can tag and generate the changelog automatically after the merge-back into main (GitCode CI / GitLab CI both work).

## 12. Code of conduct

We adopt the [Contributor Covenant 2.1](http://www.contributor-covenant.org/version/2/1/code_of_conduct/) (see `CODE_OF_CONDUCT.md` in the repository). The essentials:

- Be friendly, respectful and stay on the technical merits; personal attacks, harassment and discrimination are not tolerated.
- Disagreements are settled by public discussion plus maintainer arbitration; the maintainers have the final say on merge disputes.
- Report violations privately to a maintainer — do not start a public flame war.

## 13. Security vulnerability disclosure

**Never report a security vulnerability in a public issue** (it puts everyone at risk):

- Contact a maintainer (the owner listed in `MAINTAINER`) through GitCode **direct message**, or follow the guidance in `SECURITY.md`.
- Include the impact, trigger conditions, reproduction and a suggested fix; **do not publish a PoC**.
- Maintainers will assess and fix it without leaking details (in the next hotfix / weekly release) and credit you in the release notes.

## 14. Community support and communication

- Main repository: gitcode.com/grape-dev/grape ; issues and discussions live in the repository's issue tracker.
- Related repositories: official skills `grape-dev/grape-skills`, project templates `grape-dev/grape-template`.
- Feishu groups: organisations running Grape can give feedback directly in their bound group.

## 15. FAQ

- **Why didn't my MR make it into main?** — The target branch should be the current `weekly-0X`; it is merged back on Friday.
- **What about work started after Friday?** — Branch `weekly-02` off the new main next Monday; this week's release is unaffected.
- **I wrote code but never claimed an issue?** — Add it to the MR description; it will be settled during review.
- **Feeling stuck?** — Comment on the issue/MR and @ a maintainer; don't go it alone.

## 16. Newcomer path (good first issue)

1. Look for issues labelled `good-first-issue` (usually docs, missing tests, small tools, edge cases).
2. You can contribute without touching code: see [§17.4].
3. Start small: one docs/test/tool MR is enough to get a feel for the collaboration.

## 17. Contributor notes

### 17.1 Sign-off (DCO)

We follow the **Developer Certificate of Origin (DCO)** model: every commit carries `Signed-off-by: <name> <email>` (`git commit -s`), which states that you confirm the contribution is your own work or that you have the right to contribute it under the project license (MIT). Maintainers verify that every commit in an MR is signed off.

### 17.2 Copyright and license

The code follows this repository's `LICENSE` (MIT). Contributing means agreeing to distribute it under that license.

### 17.3 Consistency guidance

- New documentation should be bilingual or at least in Chinese; keep terminology aligned with the README (Skill / Agent / Pipeline, etc.).
- Design documents live in `docs/` (named `xxx-design.md`); read the relevant one before touching a large module.

### 17.4 Contributing without writing code

- **Documentation**: improve the README, extend or correct design docs and comments.
- **Skills**: contribute new Skills to `grape-dev/grape-skills` (`skills/<agent_type>/<skill>/`, Markdown only — no backend changes needed). This is the project's "low barrier, high value" direction.
- **Project templates**: add one-click templates to `configs/project-templates.json`.
- **Bug reports**: a clear reproduction plus logs (see §3).
- **Test cases**: add cases covering edge scenarios (raising coverage is a direct contribution).
- **Community**: answer questions, write tutorials, maintain non-code assets.

---

Questions? Open an issue or ask directly in the Feishu group. We look forward to your contribution — welcome to the Grape community.
