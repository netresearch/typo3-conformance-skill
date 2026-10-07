<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
<!-- SPDX-FileCopyrightText: Netresearch DTT GmbH -->

# Extension Title and Description Across Platforms

An extension's human-readable name appears on TER, in the TYPO3 Extension
Manager, on docs.typo3.org, on Packagist, on GitHub and in the README. Each
place reads it from a different field, so the fields drift apart unless one
title and one description are set in every one of them.

## Where each place reads the name

| Place | Source field | Length and rendering |
|---|---|---|
| TER detail page H1, search results, RSS, REST API `title`, browser tab | `composer.json` `description`: the part before the first ` - `. Without ` - `: `title` in `ext_emconf.php`, or the whole description when that is empty | Stored in a 255-byte column; a longer title fails the upload. Not cropped. |
| TER description | the part after the first ` - `; without ` - ` the `ext_emconf.php` `description` | Search card crops it at 220 characters. |
| TER author and company | composer `authors[0]` name; company from `ext_emconf.php` only | Search card crops the author at 50 characters. |
| TYPO3 v14 Extension Manager | as TER (`Package.php`, since v14.0.0). Without ` - ` and without `ext_emconf.php`: the whole description | Not cropped. |
| TYPO3 v13 Extension Manager, Composer mode | the **whole** composer `description`; v13 does not split | Not cropped. |
| TYPO3 v13 Extension Manager, classic mode | `ext_emconf.php` `title` | — |
| Extension Manager description tooltip (v13, v14) | `ext_emconf.php` `description` | Hover only. |
| docs.typo3.org header bar, menu caption, start page H1 | first heading of `Documentation/Index.rst` | Not cropped. The menu caption wraps from about 26 characters, the H1 from about 43 characters at 1024 px and about 20 at 390 px. |
| docs.typo3.org browser tab | `Documentation/guides.xml` `<project title>` | — |
| Packagist | heading: package name. Below it: the whole composer `description` of the default branch | Shown verbatim, ` - ` included. |
| GitHub | heading: repository name. "About": the repository description setting | At most 350 characters. Also the browser tab and link previews. |
| README | first heading | — |

Sources: TER `extensions/ter_fe2/Classes/Utility/ComposerManifestUtility.php`
`getTitleAndDescription()` and `ext_tables.sql`; TYPO3
`typo3/sysext/core/Classes/Package/Package.php` at v13.4.35 and v14.3.7;
render-guides `packages/typo3-docs-theme` templates
`structure/navigation/navigationHeader.html.twig`,
`structure/document.html.twig`, `structure/layout.html.twig`. The wrap
widths were measured in Chromium on a live manual and shift by a few
characters with other glyphs.

## Rules

1. **One title.** The same string in `ext_emconf.php` `title`, before ` - `
   in `composer.json` `description`, in `guides.xml` `<project title>`, in
   the first heading of `Documentation/Index.rst` and in the
   `|extension_name|` substitution of `Documentation/Includes.rst.txt`.
2. **No vendor and no "TYPO3" in the title.** TER shows the owner,
   Packagist and GitHub show the vendor, and every place except README and
   GitHub is TYPO3 context already.
3. **Length:** at most 30 characters as the target, 40 as the limit. 30
   keeps the docs menu caption at two lines at most; 40 keeps the docs H1 on
   one line at 1024 px.
4. **One description.** The same sentence in `ext_emconf.php` `description`
   and after ` - ` in `composer.json`. No "by `<vendor>`": TER shows the
   author in its own field. Keep it under 200 characters: the TER search card
   crops at 220, and TYPO3 v13 in Composer mode shows the whole
   `composer.json` description as the title.
5. **`composer.json` description:** `<Title> - <Description>`, with no other
   ` - ` inside the title.
6. **README heading:** `<Title> for TYPO3`. On GitHub the reader has no
   TYPO3 context.
7. **GitHub "About":** `<Title> for TYPO3 - <Description>`.

Allowed to differ: backend module and dashboard widget labels (they name a
function, not the extension), the repository name, and the Composer package
name.

## Setting each field

| Field | How | Takes effect |
|---|---|---|
| `ext_emconf.php`, `composer.json` | commit | TER and the Extension Manager: with the next TER upload or installed version. Packagist: on the next default-branch update. |
| `guides.xml`, `Index.rst`, `Includes.rst.txt` | commit | docs.typo3.org: on the next render of that version. |
| README | commit | immediately on GitHub |
| GitHub "About" | `gh repo edit <owner>/<repo> --description '<Title> for TYPO3 - <Description>'` | immediately |

Check one extension:

```bash
jq -r .description composer.json | awk -F ' - ' '{ print "composer title: " $1 }'
php -r '$_EXTKEY="x"; $EM_CONF=[]; include "ext_emconf.php"; echo "emconf title:   ", reset($EM_CONF)["title"], "\n";'
grep -o '<project[^>]*title="[^"]*"' Documentation/guides.xml
awk 'NR>1 && /^[=#*~-]{3,}$/ && prev!~/^[=#*~-]*$/ && prev!~/^\.\./ { print "Index.rst H1:   " prev; exit } { prev=$0 }' Documentation/Index.rst
gh repo view --json description --jq .description
```

Checkpoints TC-186 to TC-193 check rules 1 to 6; `composer-validation.md`
covers the ` - ` form.
