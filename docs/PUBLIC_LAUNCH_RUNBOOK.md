# Clean public launch runbook

Use this runbook for the first public launch. It intentionally creates a new repository from sanitized `main`
instead of changing the existing repository in place. Closed pull-request refs in the existing private repository
can retain pre-rewrite history and must never be copied to the public repository.

This runbook does not authorize the visibility change. Stop at the explicit visibility gate until the repository
owner says to make the candidate public.

## 1. Prepare one immutable candidate

From a clean private checkout:

```powershell
git pull --rebase
python scripts/check_public_tree.py
gitleaks git --redact --log-opts="--all"
python -m pytest -q
python scripts/check_acceptance.py
python run_evidence.py
git diff --check
git status --short
git rev-parse HEAD
```

Record the final commit and tree hashes. Retain a private main-only bundle and its SHA-256 checksum outside the
repository. The bundle is rollback evidence, not an import source for the public candidate.

## 2. Build a main-only transport clone

Create a disposable clone from the final local checkout:

```powershell
$PublicStage = Join-Path $env:TEMP ("routemap-public-" + [guid]::NewGuid())
git -c core.longpaths=true clone --no-local --single-branch --branch main --no-tags . $PublicStage
git -C $PublicStage fsck --full --no-reflogs --unreachable
git -C $PublicStage show-ref
```

The per-command `core.longpaths` setting is needed when the Windows temporary-directory prefix plus a retained
research-artifact path exceeds the default checkout limit. It changes only this clone operation.

Confirm this clone contains only the intended `main` history and its `HEAD` and tree hashes match the recorded
candidate. Never use `git push --mirror`, `--all`, or `--tags`, and never restore the private backup bundle into
the replacement repository.

## 3. Preserve the old repository as a private archive

1. Close any open pull requests and delete their Dependabot branch heads.
2. Rename the existing repository to a dated `routemap-eval-harness-private-archive-*` name.
3. Keep it private, add a description warning that historical PR refs contain pre-rewrite metadata, then archive
   it. Never make this repository public.
4. Point existing private maintenance remotes at the archive URL before reusing the canonical name.
5. Do not copy collaborators, deploy keys, secrets, variables, webhooks, environments, releases, deployments,
   Actions history, or pull requests to the replacement repository without a separate review.

## 4. Create and validate the private replacement

1. Create an empty **private** `routemap-eval-harness` repository. Do not add a generated README, license,
   `.gitignore`, template, or initial commit.
2. Keep it owner-only during launch. A stale clone of the old repository could otherwise push old history under
   the reused canonical URL.
3. Configure issues on; wiki, projects, and discussions off; squash and rebase merges on; merge commits off;
   branch deletion after merge on.
4. Restrict Actions to GitHub-owned, SHA-pinned actions. Keep workflow token permissions read-only and prevent
   Actions from approving pull requests.
5. Enable the dependency graph, Dependabot alerts, and automated security updates.
6. Add the empty replacement as the transport clone's `origin`, then push exactly the recorded commit:

   ```powershell
   git -C $PublicStage remote remove origin
   git -C $PublicStage remote add origin https://github.com/OWNER/routemap-eval-harness.git
   git -C $PublicStage push --set-upstream origin FINAL_SHA:refs/heads/main
   ```

7. Set `main` as default and restore the repository description and topics.
8. Wait for both evidence jobs to pass. Inspect every Actions log and artifact because they become public with
   the repository.

Before proceeding, confirm the replacement has a different repository ID from the archive; the expected commit
and tree hashes; no old commit IDs; no pull requests, releases, deployments, secrets, variables, deploy keys, or
webhooks; no secret-scan findings; and only refs descended from the sanitized candidate.

## 5. Explicit visibility gate

Stop here. Continue only after the owner explicitly authorizes making the validated replacement public.

Immediately after changing visibility to public:

1. Enable private vulnerability reporting.
2. Verify secret scanning and push protection are enabled and have zero unresolved alerts.
3. Enable CodeQL default setup for Python and GitHub Actions; wait for its initial result before requiring its
   check by name.
4. Require approval for workflows from every external fork contributor.
5. Protect `main`: require the exact `evidence (3.10)` and `evidence (3.11)` checks, require an up-to-date branch,
   apply the rule to administrators, require a pull request with zero approvals for a solo-maintainer-safe flow,
   require linear history and resolved conversations, and prohibit force pushes and deletion.
6. After CodeQL's first successful run, add its exact reported check to branch protection.
7. Verify the license, community profile, security policy, issue forms, repository description, and topics while
   signed out.
8. Make a new anonymous clone, follow the README quick start, and confirm the installed CLI and cockpit work.

GitHub Free exposes protected branches for public repositories, public repositories receive free secret
scanning, and private vulnerability reporting is available to public-repository administrators. Visibility
changes also make existing Actions history and logs public, which is why all candidate runs are inspected first.

## 6. Rollback and incident response

Before visibility changes, rollback is recoverable: rename the failed candidate to a private dated name,
unarchive the old private repository, and restore its canonical name. Deletion is unnecessary.

After a repository becomes public, making it private again cannot retract clones, forks, cached pages, Actions
logs, or copied data. If a secret is found, revoke or rotate it first, contain repository visibility, preserve
evidence, and contact GitHub Support when cached or pull-request refs require removal.
