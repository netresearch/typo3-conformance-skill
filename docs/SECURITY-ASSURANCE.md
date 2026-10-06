<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
<!-- SPDX-FileCopyrightText: Netresearch DTT GmbH -->

# Security Assurance Case

This document states what users of the typo3-conformance skill can and cannot expect in terms of security, and argues why the expectations hold. Every claim names the file that implements it. Vulnerabilities are reported privately as described in the [organisation security policy](https://github.com/netresearch/.github/blob/main/SECURITY.md).

## What the project ships

| Part | Files | Runs code? |
|------|-------|------------|
| Skill instructions and references | `skills/typo3-conformance/SKILL.md`, `skills/typo3-conformance/references/*.md`, `commands/check.md`, `outputStyles/conformance-report.md` | No. Text an AI agent loads. |
| Checkpoints | `skills/typo3-conformance/checkpoints.yaml` | No. Data read by an assessment runner. |
| Check scripts | `skills/typo3-conformance/scripts/*.sh` | Yes. Bash, run by the user or the agent against an extension directory. |
| Configuration templates | `skills/typo3-conformance/assets/` | No. Files a user copies into an extension (PHPStan, Rector, PHP-CS-Fixer, ESLint, Stylelint, TypoScript lint, composer-unused, a TER publish workflow). |
| Repository tooling | `Build/Scripts/check-plugin-version.sh`, `Build/hooks/pre-push`, `scripts/verify-harness.sh`, `tests/test_scripts.py` | Yes, for maintainers and CI only. |

## Security requirements

1. The check scripts only read the extension they analyse. They do not run its PHP or JavaScript, install its dependencies or contact the network.
2. The check scripts write only below the analysed directory: the report goes to `.conformance-reports/`, and `generate-report.sh` keeps its temporary copy next to it.
3. The skill and its releases are delivered unmodified from this repository.
4. Pull requests run the checks listed in [README.md](../README.md#governance-and-policies). Which of them must pass before a merge is set in the branch protection of `main`, a repository setting; on 2026-10-01 it required some of them, did not apply to administrators and required no approving review.

## Actors and trust boundaries

- **User**: runs the skill or a script against an extension they chose. Trusted: they choose the target directory and the arguments.
- **AI agent**: loads `SKILL.md` and the references and runs the scripts or the grep recipes in `SKILL.md`. It acts with the user's permissions.
- **Analysed extension**: untrusted input. Its files are read with `grep`, `find`, `cat`, `awk`, file tests and `git` commands.
- **Maintainers and CI**: change and release this repository.

Boundary 1 lies between the scripts and the analysed extension: extension content is data, never code. Boundary 2 lies between this repository and the user's machine: releases are built and signed in CI.

## Argument per requirement

### 1. The check scripts do not execute the analysed code

- `check-file-structure.sh`, `check-coding-standards.sh`, `check-architecture.sh`, `check-testing.sh` and `check-documentation.sh` inspect files only with `[ -f ]`, `[ -d ]`, `find`, `grep`, `wc`, `cat` and `git rev-parse`/`git ls-files` (plus `head`, `sort`, `uniq` and `basename` on the results). None of them runs `php`, `composer`, `npm`, `eval` or `source` on anything from the target.
- `check-phpstan-baseline.sh` runs `git diff` and `git show` in the target; `check-file-structure.sh` runs `git ls-files` there. Both go through `project_git` (`scripts/lib/git.sh`), which sets `core.fsmonitor=false`, `core.hooksPath=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`; `git diff` also gets `--no-ext-diff` and `git show` `--no-textconv`, so diff drivers configured in the target do not run. `tests/test_scripts.py` (`UntrustedGitConfigTest`) covers both scripts. They do not run PHPStan; the remediation text they print tells the user which command to run.
- `generate-report.sh` evaluates `[ -f ]` tests and `grep -rq` against the target to fill the report checklist.
- `check-conformance.sh` calls only the scripts next to it (`SCRIPT_DIR`), never a script from the target.
- None of the check scripts calls `curl`, `wget`, `gh` or another network client.

### 2. Writes stay inside the analysed directory

- `check-conformance.sh` resolves the target to an absolute path, verifies it exists and contains `composer.json` or `ext_emconf.php`, and only then creates `.conformance-reports/` and writes `conformance_<timestamp>.md` there.
- `generate-report.sh` rewrites that report file in place through a `mktemp` file, which it deletes.
- The other check scripts write only to standard output.
- `tests/test_scripts.py` exercises these paths, including a relative target path, a missing directory (not created) and a directory that is not an extension (rejected before anything is written).

### 3. Delivered content is the reviewed content

- Releases are built by `.github/workflows/release.yml`, which calls the `netresearch/skill-repo-skill` release workflow with `id-token: write` and `attestations: write`. That workflow signs `SHA256SUMS.txt` keyless with `cosign sign-blob` and attests the release archives and checksums with `actions/attest-build-provenance`.
- `Build/hooks/pre-push` runs `Build/Scripts/check-plugin-version.sh`, which refuses a push where a semver tag at `HEAD` disagrees with the version in `.claude-plugin/plugin.json`. The shared Skill Validation job checks that `SKILL.md`, `plugin.json` and `.claude-plugin/plugin.json` carry the same version.
- `.github/workflows/scorecard.yml` runs OpenSSF Scorecard on `main` and weekly.

### 4. Changes pass automated checks

Every workflow declares `permissions: {}` at the top and grants each job only what its reusable workflow needs. The workflows that run on `pull_request_target` (`auto-merge-deps.yml`, `labeler.yml`, `pr-quality.yml`) are thin callers that do not check out or run pull request code; each says so in its header comment. The checks themselves are listed in [README.md](../README.md#governance-and-policies).

## Common weaknesses

| Weakness | Where it could arise | Countermeasure |
|----------|---------------------|----------------|
| CWE-78 OS command injection | File names and contents of the analysed extension | Target content reaches the tools the scripts call (`grep`, `find`, `wc`, `head`, `cat`, `awk`, `sort`, `uniq`, `basename` and `git`) only as file arguments or standard input. No script builds a command string from it or passes it to `eval`. |
| CWE-22 path traversal | The target path argument | The path is the user's own choice; `check-conformance.sh` resolves it once and writes only below it. |
| CWE-377 insecure temporary file | Report rewriting | `generate-report.sh` creates its temporary file with `mktemp` next to the report, below the analysed directory, and removes it. |
| CWE-829 inclusion from an untrusted source | Scripts from the target | `check-conformance.sh` runs sibling scripts from `SCRIPT_DIR` only. |
| CWE-1104 unmaintained third-party components | Development and CI tools | Pre-commit hooks are pinned by `rev:` in `.pre-commit-config.yaml` and updated by Renovate (`renovate.json`); the reusable workflows pin actions by commit SHA. |
| Secret exposure (CWE-798) | Commits | GitHub secret scanning with push protection (a repository setting) rejects pushes containing a recognised secret; Betterleaks scans every pull request to `main` (`security.yml`). The scripts read and store no credentials. |

## What the skill does not protect against

- **Content of the analysed extension reaching the agent.** The agent reads the extension's code and documentation. Instructions hidden in those files are text like any other; the skill does not filter them. Review the agent's proposed changes before accepting them.
- **`allowed-tools`.** `SKILL.md` declares none. Where a skill declares `allowed-tools`, it only pre-approves tools; it does not remove tools the agent already has.
- **Git configuration of the target.** `check-phpstan-baseline.sh` and `check-file-structure.sh` run `git` inside the target with its fsmonitor command, hooks and diff drivers turned off; other settings of that repository's `.git/config` still apply to these read-only git calls.
- **Report content.** Reports quote up to ten matching source lines per pattern from the analysed extension (`check-architecture.sh`) and the content of its `Build/.nvmrc` (`check-testing.sh`). Treat a report as untrusted text when it is rendered or forwarded.
- **Arguments.** The scripts trust their arguments; `generate-report.sh` expects the numeric scores `check-conformance.sh` passes.
- **Correctness of the verdict.** The scripts are pattern checks with `grep` and `find`. A passing check is not proof that an extension is secure or conformant, and the scores are an orientation, not a certification.
- **Configuration templates.** The files under `assets/` configure tools in the user's extension. Review them before copying; they are not security controls.
