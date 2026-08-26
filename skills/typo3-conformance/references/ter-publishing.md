# TER Publishing Reference

**Purpose:** Document requirements and best practices for publishing TYPO3 extensions to the TER (TYPO3 Extension Repository)

## Overview

The TYPO3 Extension Repository (TER) at [extensions.typo3.org](https://extensions.typo3.org) is the official distribution platform for TYPO3 extensions. Publishing is typically automated via GitHub Actions using the official `typo3/tailor` tool.

---

## Upload Comment Format

The "Last upload comment" field displayed on extension pages has specific format requirements:

### Allowed Content
- **Type:** Plain text only (no HTML, Markdown, or rich formatting)
- **Letters, numbers, whitespace**
- **Basic punctuation:** `" % & [ ] ( ) . , ; : / ? { } ! $ - @`
- **Newlines:** Supported and displayed as line breaks (`<br>`)

### Validation
- **Required:** Cannot be empty (throws `NoUploadCommentException`)
- **Storage:** `TEXT` field in database (no enforced length limit)

### Characters Stripped in XML Export
When exported to `extensions.xml` feed, the following regex filters the comment:
```
/[^\w\s"%&\[\]\(\)\.\,\;\:\/\?\{\}!\$\-\/\@]/u
```

**Stripped characters include:** `# * + = ~ ^ | \ < >` and non-ASCII special characters

### Rendering Contexts
| Context | Processing |
|---------|------------|
| Frontend (extension page) | `<f:format.nl2br>` - newlines become `<br>` |
| Email notifications | Raw text |
| XML feed (extensions.xml) | Sanitized via `xmlentities()` |

### Best Practices
1. **Keep it concise:** Focus on key changes
2. **Use line breaks:** Structure with newlines for readability
3. **Avoid special characters:** Stick to basic punctuation
4. **Be descriptive:** Summarize the release, not just "Bug fixes"

**Good Example:**
```
Fixed critical bug in authentication module
- Resolved token expiration issue
- Updated dependency versions
- Improved error messages for version constraints
```

**Avoid:**
```
Bug fixes & improvements! See CHANGELOG.md for details...
```
(The `&` will be escaped in the XML feed. ASCII `...` is fine — the XML-export regex above permits `.` — but the Unicode ellipsis `…` gets stripped since it's not in the allow-list.)

---

## CI TER Compatibility Check

**CRITICAL:** Add this check to your CI workflow to catch ext_emconf.php issues BEFORE release attempts!

**Add to `.github/workflows/ci.yml`:**
```yaml
- id: ter-compatibility
  name: TER Compatibility Check
  run: |
    # ext_emconf.php must NOT contain strict_types - TER cannot parse it
    # Use regex to match actual declaration (not comments mentioning it)
    if grep -qE "^[[:space:]]*declare\(strict_types" ext_emconf.php; then
      echo "::error file=ext_emconf.php::ext_emconf.php contains strict_types declaration which breaks TER publishing"
      exit 1
    fi
    echo "TER compatibility check passed"
```

**Why this matters:** This check runs on every PR and push, catching strict_types issues before they reach a release attempt. Without this, you may only discover the problem when TER upload fails.

---

## Version Synchronization Check

**CRITICAL:** The `typo3/tailor` tool rejects uploads where the tag version does not match `ext_emconf.php` `'version'`. This is a common release failure.

### The Problem

When creating a release tag (e.g. `0.4.1`), `ext_emconf.php` must already contain `'version' => '0.4.1'`. If the version was not bumped before tagging, `tailor ter:publish` fails with "configured version does not match".

GitHub.com does not support custom pre-receive hooks, so server-side tag validation is not possible. Use **defense-in-depth**: local git hook + CI validation step.

### CI Workflow Step

Add this step to your TER publish workflow **after checkout and before publishing**:

```yaml
- name: Validate ext_emconf.php version
  env:
    TAG_VERSION: ${{ env.version }}
  run: |
    EMCONF_VERSION=$(grep -oP "'version'\s*=>\s*'\K[^']+" ext_emconf.php)
    if [[ "${TAG_VERSION}" != "${EMCONF_VERSION}" ]]; then
      echo "::error file=ext_emconf.php::Tag version (${TAG_VERSION}) does not match ext_emconf.php version (${EMCONF_VERSION}). Update ext_emconf.php before tagging."
      exit 1
    fi
    echo "Version validated: ${TAG_VERSION} matches ext_emconf.php"
```

### CaptainHook Pre-Push Hook

For local protection, add a pre-push hook script that checks any semver tag at HEAD:

```bash
#!/usr/bin/env bash
set -euo pipefail

TAGS=$(git tag --points-at HEAD | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' || true)
[[ -z "${TAGS}" ]] && exit 0

EMCONF_VERSION=$(grep -oP "'version'\s*=>\s*'\K[^']+" ext_emconf.php)

while IFS= read -r TAG; do
    if [[ "${TAG}" != "${EMCONF_VERSION}" ]]; then
        echo "ERROR: Tag ${TAG} does not match ext_emconf.php version ${EMCONF_VERSION}"
        exit 1
    fi
done <<< "${TAGS}"
```

Register in `captainhook.json` under `pre-push.actions[]`:
```json
{ "action": "Build/Scripts/check-tag-version.sh" }
```

### Release Process Checklist Addition

```
[ ] ext_emconf.php version bumped BEFORE creating tag
[ ] CI validates ext_emconf.php version matches tag
[ ] Pre-push hook validates locally
```

---

## CRITICAL: Upload Comment Source

**NEVER use git tag message for upload comments!**

### The Problem

When using `gh release create`, GitHub creates a **lightweight tag** (not annotated). Lightweight tags have no message, so `git tag -n1` returns the **commit message** instead:

```bash
# BAD: Gets commit message like "chore(release): v1.2.0 (#123)"
git tag -n1 -l "v${VERSION}" | sed "s/^v[0-9.]*[ ]*//g"
```

This results in TER showing unprofessional upload comments like:
- `chore(release): v13.2.0 (#508)`
- `Merge pull request #123 from feature/xyz`

### The Solution

**Always use `github.event.release.body`** (the GitHub release notes) as the comment source:

```yaml
env:
  RELEASE_BODY: ${{ github.event.release.body }}
run: |
  if [[ -n "${RELEASE_BODY}" ]]; then
    COMMENT=$(echo "${RELEASE_BODY}" | head -c 1000)
    # Strip unsupported characters
    COMMENT=$(echo "${COMMENT}" | sed 's/[#*+=~^|\\<>]//g')
  else
    COMMENT="Released version ${VERSION}"
  fi
```

### Conformance Check

When auditing extensions, verify `publish-to-ter.yml` uses:
- ✅ `github.event.release.body` - Release notes (CORRECT)
- ✅ `github.event.release.name` - Release title (fallback)
- ❌ `git tag -n1` - Tag/commit message (WRONG)

---

## GitHub Actions Workflow

### Recommended Workflow Template

**File:** `.github/workflows/publish-to-ter.yml`

**Template:** Copy from `assets/.github/workflows/publish-to-ter.yml` (the file below is a shortened illustration — the asset template additionally includes Harden Runner, SHA-pinned actions, and the idempotency precheck/verify described in the sections after this one; copy the asset, don't retype this excerpt).

```yaml
name: Publish new extension version to TER

on:
  release:
    types: [published]

jobs:
  publish:
    name: Publish new version to TER
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: Validate tag format
        run: |
          if ! [[ "${GITHUB_REF_NAME}" =~ ^v[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            echo "::error::Invalid tag format '${GITHUB_REF_NAME}'. Expected format: v1.2.3"
            exit 1
          fi

      - name: Resolve extension key from composer.json
        id: extkey
        run: |
          KEY=$(php -r "echo json_decode(file_get_contents('composer.json'), true)['extra']['typo3/cms']['extension-key'] ?? '';")
          echo "key=${KEY}" >> "$GITHUB_OUTPUT"

      - name: Extract version
        id: version
        run: |
          # Strip 'v' prefix for TER (expects "3.0.1" not "v3.0.1")
          VERSION="${GITHUB_REF_NAME#v}"
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
          echo "Extracted version: ${VERSION}"

      - name: Prepare release comment
        id: comment
        env:
          RELEASE_BODY: ${{ github.event.release.body }}
          RELEASE_NAME: ${{ github.event.release.name }}
          RELEASE_URL: ${{ github.event.release.html_url }}
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          # Build comment from release body or name. Every value that flows
          # into this script comes from env:, never from ${{ }} interpolated
          # directly into the run: body - see "Security Hardening" below.
          if [[ -n "${RELEASE_BODY}" ]]; then
            # Character-safe truncation - `head -c` splits multi-byte UTF-8
            # sequences mid-codepoint, python3 slices by codepoint instead
            COMMENT=$(printf '%s' "${RELEASE_BODY}" | python3 -c 'import sys; sys.stdout.write(sys.stdin.read()[:1000])')
          elif [[ -n "${RELEASE_NAME}" ]]; then
            COMMENT="${RELEASE_NAME}"
          else
            COMMENT="Release ${VERSION}"
          fi

          # Strip characters not supported in TER XML export
          # Allowed: word chars, whitespace, " % & [ ] ( ) . , ; : / ? { } ! $ - @
          COMMENT=$(printf '%s' "${COMMENT}" | sed 's/[#*+=~^|\\<>]//g')

          # Append release link on new line
          COMMENT="${COMMENT}"$'\n\n'"Details: ${RELEASE_URL}"

          # Randomized delimiter, not a static "EOF" - see "Security Hardening"
          DELIMITER="ghadelim_$(openssl rand -hex 8)"
          {
            echo "comment<<${DELIMITER}"
            echo "${COMMENT}"
            echo "${DELIMITER}"
          } >> "$GITHUB_OUTPUT"

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          extensions: intl, mbstring, json, zip, curl
          tools: composer:v2

      - name: Install tailor
        run: composer global require "typo3/tailor:^2.0" --prefer-dist --no-progress

      - name: Publish to TER
        env:
          EXTENSION_KEY: ${{ steps.extkey.outputs.key }}
          TYPO3_API_TOKEN: ${{ secrets.TYPO3_TER_ACCESS_TOKEN }}
          VERSION: ${{ steps.version.outputs.version }}
          COMMENT: ${{ steps.comment.outputs.comment }}
        run: |
          TAILOR="$(composer global config bin-dir --absolute)/tailor"
          "${TAILOR}" ter:publish --comment="${COMMENT}" "${VERSION}" "${EXTENSION_KEY}"
```

### Required Secrets

| Secret | Description | Where to Get |
|--------|-------------|--------------|
| `TYPO3_TER_ACCESS_TOKEN` | API token for TER uploads | [extensions.typo3.org/my-extensions](https://extensions.typo3.org/my-extensions) |

`TYPO3_EXTENSION_KEY` is **not** needed as a secret: `tailor` resolves the extension key from `composer.json`'s `extra.typo3/cms.extension-key` when it's passed as the last positional argument (see the "Resolve extension key from composer.json" step above), which is the single source of truth already used for the same value elsewhere. Passing an extension key positional argument also takes priority over reading `composer.json`, so this stays overridable per-call without needing a secret at all.

### Tag Format Requirements
- **Format:** `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`)
- **Note:** TER expects version without `v` prefix internally
- **Validation:** Workflow should validate tag format before publishing

---

## Security Hardening

The publish workflow handles a real API credential (`TYPO3_TER_ACCESS_TOKEN`) and processes attacker-influenceable input (`github.event.release.body`/`.name`, a repository's own `CHANGELOG.md`). Apply the same hardening GitHub's own security guidance recommends for any workflow with secrets:

- **SHA-pin every third-party action**, with a version comment, e.g. `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. A floating tag (`@v4`) can be repointed by the action's maintainer (or an attacker who compromises their account) to different code without your workflow file changing.
- **Add `step-security/harden-runner`** as the first step of the job (`egress-policy: audit` is a reasonable default; tighten to `block` with an explicit allowlist once you know the egress the job needs).
- **`persist-credentials: false`** on every `actions/checkout` step, so the job's own `GITHUB_TOKEN` isn't left sitting in the git config for later steps (or a compromised dependency) to pick up.
- **Explicit least-privilege `permissions:`** — top-level `permissions: {}` plus job-level `permissions: contents: read` (this workflow only reads the repo and talks to TER via its own API token; it needs no `GITHUB_TOKEN` write scope at all).
- **Never interpolate `${{ }}` directly into a `run:` script body.** Route every context value and step output through `env:` and reference it as a shell variable (`"${VAR}"`). Interpolating directly (`"${{ github.event.release.body }}"` inside a multi-line shell script) is the classic GitHub Actions script-injection vector: a release body containing shell metacharacters becomes part of the script text itself, not just a value. Every step in the template above follows this.
- **Randomize the `$GITHUB_OUTPUT` heredoc delimiter** instead of a static `EOF`. A release body or `CHANGELOG.md` section that happens to contain a line reading exactly `EOF` would otherwise terminate the heredoc early and let the rest of that text inject additional `$GITHUB_OUTPUT` key=value pairs. `DELIMITER="ghadelim_$(openssl rand -hex 8)"` closes that gap at negligible cost.
- **Pin `typo3/tailor` to at least a major-version constraint** (`"typo3/tailor:^2.0"`), not a bare `composer global require typo3/tailor`. The publish step runs this tool with your live TER token in its environment; an unpinned install picks up whatever the latest release happens to be on every run, with no version history to audit if that ever matters.

---

## Idempotency and Verification

**Problem:** A bare `tailor ter:publish` call has no idempotency guard and no confirmation that TER actually served the version afterward. A re-triggered run (retry after a transient failure, a re-run from the Actions UI) would attempt to publish again, and the workflow's success is only ever "the API call didn't error," not "TER now serves this version."

**Precheck** (before `Publish to TER`): `curl -I` the version's own download URL and skip the publish step if it already returns `200` (confirmed reliable from a real GitHub Actions runner, not just locally — see the caveat below):

```yaml
- name: Check if version is already on TER
  id: precheck
  env:
    KEY: ${{ steps.extkey.outputs.key }}
    VERSION: ${{ steps.version.outputs.version }}
  run: |
    URL="https://extensions.typo3.org/extension/download/${KEY}/${VERSION}/zip"
    STATUS=$(curl -sS -o /dev/null -w '%{http_code}' -I --max-time 15 "${URL}" || echo "000")
    if [[ "${STATUS}" == "200" ]]; then
      echo "already-published=true" >> "$GITHUB_OUTPUT"
    else
      echo "already-published=false" >> "$GITHUB_OUTPUT"
    fi
```

Guard the publish step with `if: steps.precheck.outputs.already-published != 'true'`.

**Verify** (after `Publish to TER`, unconditional — it should pass immediately on a skip too): poll the same URL with a bounded timeout instead of trusting the API call's exit code alone:

```yaml
- name: Verify TER serves the version
  env:
    KEY: ${{ steps.extkey.outputs.key }}
    VERSION: ${{ steps.version.outputs.version }}
  run: |
    URL="https://extensions.typo3.org/extension/download/${KEY}/${VERSION}/zip"
    DEADLINE=$(( $(date +%s) + 600 ))
    while true; do
      STATUS=$(curl -sS -o /dev/null -w '%{http_code}' -I --max-time 15 "${URL}" || echo "000")
      [[ "${STATUS}" == "200" ]] && exit 0
      [[ $(date +%s) -ge ${DEADLINE} ]] && { echo "::error::Timed out waiting for TER to serve ${VERSION}"; exit 1; }
      sleep 30
    done
```

**Caveat on trusting this check:** the download URL returns `303` (redirecting to the extension's overview page) for a version that genuinely isn't published yet, and `200` once it is — this is verified against real production Actions logs of an existing Netresearch extension (precheck logged `303` before publish, verify logged `200` on the first attempt right after). Testing this specific check by hand from an arbitrary machine or with a non-default `curl` User-Agent can give inconsistent results (bot-protection on the TER frontend), so don't use ad-hoc manual `curl` probing to judge whether this pattern "works" — trust the actual GitHub Actions run logs instead.

---

## CHANGELOG.md as a Comment Source

Prefer the repository's own `CHANGELOG.md` section for the released version over the GitHub release body, when one exists: it's curated, already committed at tag time, and — critically — it's the only source that has real content on a `workflow_dispatch` re-run (see below), where `github.event.release.*` doesn't exist at all.

For a changelog following [Keep a Changelog](https://keepachangelog.com/) (`## [1.2.3] - 2024-01-01` headings, `### Added`/`### Fixed` subsections):

```bash
COMMENT=$(awk -v ver="${VERSION}" '
  { sub(/\r$/, "") }
  /^## / {
    if (found) { exit }
    line = $0
    sub(/^## *\[?v?/, "", line)
    sub(/\]?( .*)?$/, "", line)
    if (line == ver) { found = 1 }
    next
  }
  found { print }
' CHANGELOG.md | sed -e '/./,$!d')
```

The leading `{ sub(/\r$/, "") }` rule strips a trailing `\r` from every line before matching — without it, a CRLF-saved `CHANGELOG.md` (e.g. edited on Windows) leaves the heading as `"1.2.3\r"`, which never equals `"1.2.3"`, and the extraction **silently** falls through to whatever fallback comment source is next in the chain. Verify this extraction against your own file's actual heading convention if it differs from Keep a Changelog (some projects use a bare `# 1.2.3` per version with no brackets/date) — adjust the two `sub()` patterns accordingly and test with `awk` directly against the real file for the first version, the last version (no following `## ` line to terminate on), and a nonexistent version (must produce empty output, not an error).

When stripping unsupported characters from a `### Fixed`-style subsection heading, strip the leading `#`s as one unit first, not as part of the same character class as the other disallowed characters — `sed 's/[#*+=~^|\\<>]//g'` turns `"### Fixed"` into `" Fixed"` (an orphaned leading space, no visible heading), not `"Fixed"`. Do the heading strip as its own pass before the character-class strip:

```bash
COMMENT=$(printf '%s' "${COMMENT}" | sed -E 's/^#+[[:space:]]*//; s/[*+=~^|\\<>]//g')
```

---

## Manual Republish via workflow_dispatch

Add a `workflow_dispatch` trigger so an already-tagged version can be re-published on demand (e.g. to correct the upload comment, or to publish a version whose original release-triggered run failed):

```yaml
on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      tag:
        description: 'Git tag to (re)publish, e.g. v1.2.3 (must already exist)'
        required: true
        type: string
```

Two things this needs beyond just adding the trigger:

1. **Resolve the target version from the dispatch input, not `GITHUB_REF_NAME`.** On `workflow_dispatch`, `GITHUB_REF_NAME` is the branch the workflow was dispatched against, not the tag to publish — only `github.event.inputs.tag` carries it. `VERSION="${DISPATCH_TAG:-${GITHUB_REF_NAME}}"` (with `DISPATCH_TAG` from `env:`) covers both trigger types in one step.
2. **Verify the input is a real tag, not a same-named branch**, after checkout: validating the *format* of the input (`^v[0-9]+\.[0-9]+\.[0-9]+$`) is not the same as confirming it's an actual tag. Anyone able to trigger `workflow_dispatch` (repo write access) could otherwise push a branch named e.g. `v9.9.9` and get its unreviewed content checked out and published, bypassing whatever review gate normally applies to creating a real release. `git ls-remote --tags --exit-code origin "refs/tags/${DISPATCH_TAG}"` checks against the remote directly, independent of how `actions/checkout` happened to resolve the ambiguous ref locally.
3. **Bypass the idempotency precheck on `workflow_dispatch`** (`if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then ... force publish ...`) — the whole point of a manual re-run is usually to correct something on an already-published version, and TER's own re-upload behavior (see the Troubleshooting table) makes that safe.

See `assets/.github/workflows/publish-to-ter.yml` for the full implementation including all three points.

---

## MANDATORY: TER Metadata Setup (Sidebar Links)

**CRITICAL:** The TER extension page sidebar links (Extension Manual, Found an Issue?, Code Insights, Packagist.org) are **NOT** populated from `composer.json`. They must be set explicitly via `tailor ter:update`.

Without this step, the TER page looks incomplete — no links to documentation, issues, source code, or Packagist.

### The Problem

New extensions uploaded to TER show an empty sidebar with no links:
- No "Extension Manual" button
- No "Found an Issue?" button
- No "Code Insights" button
- No "Packagist.org" button

This makes the extension appear unprofessional and hard to use.

### The Solution

Run `tailor ter:update` after the first TER upload:

```bash
TYPO3_API_TOKEN=your-token tailor ter:update \
  --composer="vendor/package-name" \
  --manual="https://github.com/vendor/repo" \
  --issues="https://github.com/vendor/repo/issues" \
  --repository="https://github.com/vendor/repo" \
  --tags="tag1,tag2,tag3" \
  extension_key
```

### Available Metadata Fields

| Option | TER Sidebar Button | Required |
|--------|--------------------|----------|
| `--manual` | Extension Manual | **YES** |
| `--issues` | Found an Issue? | **YES** |
| `--repository` | Code Insights | **YES** |
| `--composer` | Packagist.org (auto-linked) | **YES** |
| `--tags` | Search tags | Recommended |
| `--paypal` | Sponsoring link | Optional |

### When to Run

- **First release:** MANDATORY after the first `ter:publish`
- **URL changes:** Only when repository, docs, or issue tracker URLs change
- **Links persist:** Once set, they carry across all future version uploads

### Automation via CI

Add to your TER publish workflow as a post-publish step:

```yaml
- name: Update TER metadata
  if: env.FIRST_RELEASE == 'true'  # or always, idempotent
  run: |
    TAILOR="$(composer global config bin-dir --absolute)/tailor"
    "${TAILOR}" ter:update \
      --composer="${COMPOSER_NAME}" \
      --manual="${REPO_URL}" \
      --issues="${REPO_URL}/issues" \
      --repository="${REPO_URL}" \
      "${TYPO3_EXTENSION_KEY}"
```

### Verification

After setting metadata, verify on the TER page:

```bash
# Check that all 4 sidebar links are present
curl -s "https://extensions.typo3.org/extension/${EXT_KEY}" | \
  grep -c 'Extension Manual\|Found an Issue\|Code Insights\|Packagist\.org'
# Expected: 4
```

---

## Packagist Listing

Extensions with a `composer.json` should be listed on [Packagist](https://packagist.org):

1. **Submit package** at https://packagist.org/packages/submit
2. **Enable auto-update** via GitHub webhook (Packagist Settings > Enable GitHub Hook)
3. **Verify** the package appears with correct description and version

The `--composer` flag in `ter:update` creates the Packagist link on the TER page.

---

## Documentation Rendering on docs.typo3.org

Extensions with a `Documentation/` directory and `guides.xml` can have their documentation rendered at docs.typo3.org:

1. **Create** `Documentation/guides.xml` with project metadata
2. **Add RST files** following TYPO3 documentation standards
3. **Webhook** is automatically triggered when the extension is on Packagist
4. **Verify** at `https://docs.typo3.org/p/vendor/package-name/main/en-us/`

If not using docs.typo3.org, set `--manual` to the GitHub repository URL or a hosted documentation site.

---

## Release Comment Best Practices

### Writing Effective Release Notes

**Structure:**
```
Brief summary of the release (one line)

- Key change 1
- Key change 2
- Key change 3
```

**Do:**
- Start with a clear summary line
- Use bullet points for individual changes
- Group by type (Features, Fixes, Breaking)
- Keep each point concise
- Include TYPO3 version compatibility changes

**Don't:**
- Use Markdown formatting (not rendered)
- Use special characters like `#`, `*`, `<`, `>`
- Write excessively long descriptions
- Just say "Bug fixes" without details

### Example Release Notes

**Good:**
```
TYPO3 13 compatibility and performance improvements

Breaking changes:
- Minimum PHP version is now 8.2
- Removed deprecated API methods

New features:
- Added support for native lazy loading
- Improved caching for list views

Bug fixes:
- Fixed pagination in backend module
- Resolved translation loading issue
```

**Transformed for TER:**
```
TYPO3 13 compatibility and performance improvements

Breaking changes:
- Minimum PHP version is now 8.2
- Removed deprecated API methods

New features:
- Added support for native lazy loading
- Improved caching for list views

Bug fixes:
- Fixed pagination in backend module
- Resolved translation loading issue

Details: https://github.com/vendor/extension/releases/tag/v2.0.0
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "No upload comment" error | Empty comment passed to tailor | Ensure fallback comment in workflow |
| Special characters in XML feed | Unsupported chars in comment | Strip `#*+=~^|\\<>` from comments |
| Version mismatch | Tag doesn't match ext_emconf | Use `tailor set-version` before publish |
| Authentication failed | Invalid/expired API token | Regenerate token at extensions.typo3.org |
| Published with wrong / outdated upload comment | Publish ran before the release body was finalized | Re-run `tailor ter:publish --comment "..." vX.Y.Z` on the same version — TER overwrites the upload comment on republish. The ZIP contents are unchanged (the version number doesn't let you ship different code under the same version), only the comment updates. Safe to re-trigger the publish workflow after editing the GitHub release body. |

### Validation Script

Add to your workflow for pre-publish validation:
```bash
# Validate upload comment format
validate_comment() {
  local comment="$1"

  # Check not empty
  if [[ -z "${comment// }" ]]; then
    echo "::error::Upload comment cannot be empty"
    return 1
  fi

  # Check for unsupported characters
  if [[ "$comment" =~ [#*+=~^\|\\<>] ]]; then
    echo "::warning::Comment contains characters that will be stripped in XML export"
  fi

  return 0
}
```

---

## Technical Details

### TER API Endpoints
- **SOAP API:** Legacy, still supported (`ter_soap` extension)
- **REST API:** Modern interface (`ter_rest` extension)

### Comment Processing Pipeline
1. **Input:** Raw text from tailor CLI
2. **Validation:** Non-empty check (`ExtensionVersion.php`)
3. **Storage:** `TEXT` field in `tx_terfe2_domain_model_version`
4. **Frontend:** Fluid template with `<f:format.nl2br>`
5. **XML Export:** `xmlentities()` sanitization

### Source Code References (TER codebase)
- Validation: `extensions/ter/Classes/Api/ExtensionVersion.php:350`
- Storage: `extensions/ter_fe2/ext_tables.sql:84`
- TCA: `extensions/ter_fe2/Configuration/TCA/tx_terfe2_domain_model_version.php:80`
- Frontend: `extensions/ter_fe2/Resources/Private/Templates/Extension/Show.html:132`
- XML Export: `extensions/ter_fe2/Classes/Service/ExtensionIndexService.php:192`

---

## Conformance Checklist

### TER Publishing Excellence Indicators

```
GitHub Actions Workflow:
[ ] publish-to-ter.yml exists in .github/workflows/
[ ] Triggers on release published event
[ ] Validates tag format (vX.Y.Z)
[ ] Extracts version correctly (strips 'v' prefix)
[ ] Handles release body for comment
[ ] Has fallback comment if body empty
[ ] Uses typo3/tailor for publishing
[ ] Secrets properly configured (TYPO3_TER_ACCESS_TOKEN only - extension key from composer.json)

Security Hardening:
[ ] Every third-party action is SHA-pinned with a version comment
[ ] step-security/harden-runner is the first step of the job
[ ] persist-credentials: false on every checkout step
[ ] Explicit least-privilege permissions: (top-level {} + job-level contents: read)
[ ] No ${{ }} expression interpolated directly into a run: script body (env: only)
[ ] $GITHUB_OUTPUT heredoc delimiter is randomized, not a static EOF
[ ] typo3/tailor is pinned to at least a major-version constraint

Idempotency and Verification:
[ ] Precheck skips publish if the version already returns 200 from the TER download URL
[ ] Post-publish step polls (bounded timeout) until TER actually serves the version
[ ] workflow_dispatch input is verified as a real git tag (git ls-remote), not just format-validated

TER Metadata (MANDATORY for initial setup):
[ ] tailor ter:update --manual has been run (Extension Manual link)
[ ] tailor ter:update --issues has been run (Found an Issue link)
[ ] tailor ter:update --repository has been run (Code Insights link)
[ ] tailor ter:update --composer has been run (Packagist.org link)
[ ] All 4 sidebar links visible on extensions.typo3.org

Public Listings:
[ ] Extension page exists on extensions.typo3.org
[ ] Package exists on packagist.org
[ ] Documentation available (docs.typo3.org or linked from TER)
[ ] composer.json has support.issues URL
[ ] composer.json has support.source URL
[ ] composer.json has homepage URL

Release Process:
[ ] Semantic versioning followed
[ ] CHANGELOG.md updated before release
[ ] ext_emconf.php version bumped and committed BEFORE tagging
[ ] CI validates ext_emconf.php version matches tag (early fail)
[ ] composer.json version (if present) matches tag
[ ] Release notes follow TER format guidelines
[ ] Pre-push hook validates ext_emconf.php version locally
```

---

## Resources

- **Tailor CLI:** https://github.com/TYPO3/tailor
- **TER API Documentation:** https://extensions.typo3.org/help/api
- **Extension Registration:** https://my.typo3.org
- **TER Frontend:** https://extensions.typo3.org
