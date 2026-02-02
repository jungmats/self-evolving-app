# SETUP.md — Install the Self‑Evolving Substrate into an Application Repo (Option 1)

This guide installs the “workflow bundle” **by copying it into your application repository**. After setup, *all* Issues/PRs/commits happen in the app repo; the workflow repo stays clean and reusable.

---

## 0) What you are creating

You will end up with:

- **App repository** (your product): code + Issues + PRs + releases + deployments
- **Installed substrate** (copied in): GitHub Actions workflows, scripts, label schema, policy/gates, docs

---

## 1) Prerequisites

### 1.1 GitHub permissions
You need admin access to the app repo to:
- enable GitHub Actions
- configure workflow permissions
- add repository secrets/variables
- configure branch protection rules
- create GitHub Environments (for approvals)

### 1.2 Local tools (recommended)
- `git`
- GitHub CLI (`gh`) *(optional but helpful)*

### 1.3 Tokens / secrets you must provide
At minimum:
- **`GH_PAT`**: a fine-scoped Personal Access Token (classic or fine‑grained) used by workflows to manage Issues/PRs/labels.

> Security note: do **not** expose secrets to untrusted PRs (e.g., forks). Keep the repo private at first or restrict workflows appropriately.

---

## 2) Create your application repository

1. Create a new GitHub repo, e.g. `my-self-evolving-app`.
2. Clone locally and add a minimal starting app (anything that can run + can be tested).
3. Push an initial commit to `main`.

Recommended minimum:
- a “hello world” endpoint
- a minimal test suite (`pytest`, `vitest`, etc.)
- CI can run tests deterministically

---

## 3) Install the substrate (copy the workflow bundle)

### 3.1 Choose a substrate version
Pick a tagged version from the workflow repository, e.g. `v0.3.0`.

### 3.2 Copy these directories into your app repo
Copy from the workflow repo **release/tag** into the root of your app repo:

- `.github/workflows/`
- `.github/ISSUE_TEMPLATE/` *(or `.github/ISSUE_TEMPLATE/*.yml` issue forms)*
- `scripts/`
- `policy/`
- `docs/` *(optional but recommended)*

Commit the result:

```bash
git add .github scripts policy docs
git commit -m "Install self-evolving substrate vX.Y.Z"
git push
```

---

## 4) Configure GitHub repository settings

### 4.1 Actions: workflow permissions
In **Settings → Actions → General → Workflow permissions**:

- ✅ **Read and write permissions**
- ✅ Allow GitHub Actions to create and approve pull requests *(only if you need it; otherwise keep it off)*

### 4.2 Add secrets
In **Settings → Secrets and variables → Actions → Secrets** add:

- `GH_PAT`

### 4.3 Add repository variables (recommended)
In **Variables**, add:

- `SUBSTRATE_VERSION = vX.Y.Z`
- `POLICY_PROFILE = default` *(or your chosen profile)*

### 4.4 Branch protection (highly recommended)
In **Settings → Branches → Branch protection rules** for `main`:

- ✅ Require a pull request before merging
- ✅ Require approvals (min 1)
- ✅ Require status checks to pass (tests, lint, etc.)
- ✅ Restrict who can push to matching branches (optional but safer)

### 4.5 Environments for human approvals
Create **Environments**:

1. `env-implement`
   - Add required reviewers (the humans who approve implementation start)
2. `env-deploy`
   - Add required reviewers (the humans who approve deployments)

Your workflows should reference these environments in the correct stages (implementation/deploy gating).

---

## 5) Bootstrap labels + validate the state machine

The system relies on consistent labels (especially `stage:*`) and expects **exactly one `stage:*` label per Issue**.

### 5.1 Run the bootstrap workflow
Go to **Actions → Bootstrap (or “substrate-bootstrap”) → Run workflow**.

Expected outcome:
- all required labels are created/updated
- label descriptions/colors are normalized
- a schema/version marker is written (repo variable or file, depending on implementation)

### 5.2 Sanity checks (what to look for)
Open the repo’s **Labels** page and confirm you have:
- `stage:*` labels (triage/plan/prioritize/awaiting-implementation-approval/implement/pr-opened/awaiting-deploy-approval/…)
- request labels like `request:bug`, `request:feature`, `request:investigate`
- `source:*` labels like `source:user`, `source:monitor`
- `priority:*` labels (if used)

---

## 6) Configure policy & gates (per app)

Edit `policy/policy.yml` (or your equivalent) in the app repo to encode:

- product vision + non-goals
- what counts as “meta-change” (e.g., workflow/policy edits)
- allowed file paths / operations for the agent
- risk thresholds
- required test coverage expectations

Commit and push the policy config.

> Best practice: protect `policy/` and `.github/` changes via CODEOWNERS or stricter review rules.

---

## 7) Verify end-to-end with a test Issue

Create a new GitHub Issue (or create one through your app UI) with labels:

- `request:feature`
- `source:user`
- `stage:triage`

Example: **“Add /health endpoint”**

Expected automation sequence (high level):
1. **Triage** workflow runs → posts a triage comment → moves to `stage:plan`
2. **Plan** workflow runs → posts an implementation plan (including tests) → moves to `stage:prioritize`
3. **Prioritize** workflow runs → assigns `priority:*` → moves to `stage:awaiting-implementation-approval`
4. A human approves (environment `env-implement`) → issue moves to `stage:implement`
5. **Implement** workflow creates a PR and runs tests → issue moves to `stage:pr-opened`
6. Human reviews/merges PR → issue moves to `stage:awaiting-deploy-approval`
7. Human approves deploy (environment `env-deploy`) → deploy workflow runs

If anything breaks:
- check Action logs first
- confirm secrets exist
- confirm workflow permissions are “Read and write”
- confirm the Issue has exactly one `stage:*` label

---

## 8) Upgrading the installed substrate

Because you installed by copying, upgrades are explicit (and auditable).

Recommended upgrade process:
1. Create a new branch: `chore/upgrade-substrate-vA-to-vB`
2. Copy the new substrate version files over (same directories as install)
3. Commit + open PR
4. Treat substrate changes as “meta-changes” → require human approval
5. Merge only after CI passes

Optional: add a helper workflow like `substrate-upgrade.yml` that opens the upgrade PR automatically.

---

## 9) Operational notes (practical guardrails)

- Keep `main` protected; never allow agents to push directly.
- Keep deploy workflow behind environment approval.
- Pin external actions and dependencies to versions/tags.
- Make rollbacks boring: keep a clear path to redeploy the last known-good revision.

---

## Appendix: Minimal directory structure (example)

```
my-self-evolving-app/
  app/                      # your application code
  policy/
    policy.yml
  scripts/
    bootstrap_labels.*
    transition_stage.*
    run_policy_gate.*
  .github/
    workflows/
      bootstrap.yml
      triage.yml
      plan.yml
      prioritize.yml
      implement.yml
      deploy.yml
    ISSUE_TEMPLATE/
      bug.yml
      feature.yml
  docs/
    SETUP.md
```

---

If you maintain the workflow repository, keep this `docs/SETUP.md` there and treat it as the canonical onboarding path.
