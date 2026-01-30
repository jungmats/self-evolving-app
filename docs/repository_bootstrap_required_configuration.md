## Repository Bootstrap & Required Configuration

This repository contains GitHub Actions workflows that **automatically evolve an application**.
Before the workflows can run correctly, the repository must be configured as described below.

---

### 1. Create a GitHub Personal Access Token (PAT)

The bootstrap script uses the GitHub REST API and requires a short‑lived Personal Access Token (PAT).

Create a **fine‑grained PAT**:

1. Go to:

   ```
   Home → Settings → Developer Settings → Personal access tokens → Fine‑grained tokens
   ```
2. Click **Generate new token**
3. Configure the token:

   * **Repository access:** Only select this repository
   * **Permissions:**

     * Metadata → Read (required)
     * Issues → Read and write
4. Generate the token and **copy the value** (it will not be shown again).

Export the token locally as an environment variable:

```bash
export GITHUB_TOKEN="<your_pat_value>"
```

> This token is used **only locally** for repository bootstrap. Do not add it to GitHub Secrets.

---

### 2. Bootstrap GitHub Labels (one-time)

Labels are GitHub metadata and are **not stored in the repository**. They must be created via the GitHub API.

Run the bootstrap script locally:

```bash
python3 scripts/bootstrap_github.py --repo jungmats/self-evolving-app
```

Verify that labels exist:

* [https://github.com/jungmats/self-evolving-app/labels](https://github.com/jungmats/self-evolving-app/labels)

> The script is idempotent and safe to re-run.

---

### 2. Enable GitHub Actions Permissions

Workflows need permission to create issues, apply labels, post comments, and open pull requests.

Go to:

```
Settings → Actions → General
```

Set:

* **Workflow permissions** → ✅ Read and write permissions

---

### 3. Configure Branch Rules (Rulesets)

This project uses **merge to `main` = deployment approval**.
Branch rules enforce this mechanically.

Go to:

```
Settings → Rules → Rulesets → New ruleset → Branch ruleset
```

Configure:

* **Ruleset Name:** `Basic Rule Set`
* **Enforcement status:** Active
* **Bypass list:** empty
* **Target branches:** Include → default branch

Enable the following rules:

* ✅ Restrict deletions
* ✅ Block force pushes
* ✅ Require a pull request before merging
* ❌ Require status checks to pass *(enable later, once CI exists)*

> ⚠️ Status checks cannot be required until a CI workflow exists.
> Revisit this section after adding CI and enable required status checks then.

---

### 4. Configure Secrets and Variables

Workflows require secrets for LLM access and deployment.

Go to:

```
Settings → Secrets and variables → Actions
```

#### Required Secrets (Repository-level)

* `ANTHROPIC_API_KEY`
  API key used by Claude workflows (triage, planning, prioritization, implementation).

---

#### Required Secrets (Deployment)

Prefer storing deployment secrets under the `production` environment:

```
Settings → Environments → production → Environment secrets
```

* `DEPLOY_SSH_PRIVATE_KEY`
  SSH private key for the deploy user (no passphrase, or handled explicitly).
* `DEPLOY_HOST`
  Server hostname or IP.
* `DEPLOY_USER`
  SSH user (e.g. `deploy`).
* `DEPLOY_KNOWN_HOSTS`
  Output of `ssh-keyscan -H <host>` (prevents trusting unknown hosts).

---

#### Optional Variables (Convenience)

These are non-sensitive and may be added as variables:

* `DEPLOY_BASE_DEPLOYMENT_PATH` (e.g. `/srv/app`)
* `PYTHON_VERSION`
* `NODE_VERSION`

---

### Summary

After completing the steps above:

* Workflows can apply labels and manage issues/PRs
* Only PR merges can update `main`
* Merging a PR automatically triggers deployment
* Secrets are available for Claude and deployment
* The repository is ready for autonomous evolution workflows

---

### Post-CI TODO

Once a CI workflow exists and produces status checks:

1. Go to:

   ```
   Settings → Rules → Rulesets → Basic Rule Set
   ```
2. Enable **Require status checks to pass**
3. Select the CI check(s) to enforce

This tightens the merge gate to: **PR + passing tests = deploy**.
