#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Netresearch DTT GmbH
"""Behaviour tests for the shell scripts this repository ships.

Each test builds a small TYPO3 extension (or git repository) in a temporary
directory, runs one script as a subprocess and checks its exit code and the
lines it prints. Standard library only; run with ``python3 tests/test_scripts.py``.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "typo3-conformance" / "scripts"

# Isolate git from the developer's configuration (signing, hooks, templates).
ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}
ENV.pop("GITHUB_ACTIONS", None)

CONTROLLER = """<?php

declare(strict_types=1);

namespace Vendor\\Demo\\Controller;

/**
 * Demo controller.
 */
final class DemoController
{
    public function __construct()
    {
    }
}
"""

BASELINE = """parameters:
    ignoreErrors:
        -
            message: '#^First error\\.$#'
            count: {first}
            path: ../Classes/A.php
        -
            message: '#^Second error\\.$#'
            count: {second}
            path: ../Classes/B.php
"""


def run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=cwd,
        env=ENV,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True, timeout=60
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_extension(root: Path) -> Path:
    """Create an extension that passes every check script."""
    write(
        root / "composer.json",
        '{"require-dev": {"typo3/testing-framework": "^9", "phpunit/phpunit": "^11"}}\n',
    )
    write(root / "ext_emconf.php", "<?php\n$EM_CONF[$_EXTKEY] = [];\n")
    write(root / "Classes" / "Controller" / "DemoController.php", CONTROLLER)
    write(
        root / "Configuration" / "Services.yaml",
        "services:\n  _defaults:\n    autowire: true\n    autoconfigure: true\n",
    )
    (root / "Resources" / "Private").mkdir(parents=True)
    (root / "Resources" / "Public").mkdir(parents=True)
    write(root / "Tests" / "Unit" / "Controller" / "DemoControllerTest.php", "<?php\n")
    write(root / "Tests" / "Functional" / "DemoTest.php", "<?php\n")
    write(root / "Build" / "phpunit" / "UnitTests.xml", "<phpunit/>\n")
    write(root / "Build" / "phpunit" / "FunctionalTests.xml", "<phpunit/>\n")
    write(root / "Documentation" / "Index.rst", "Demo\n====\n")
    write(root / "Documentation" / "guides.xml", "<guides/>\n")
    return root


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class FileStructureTest(TempDirTestCase):
    script = SCRIPTS / "check-file-structure.sh"

    def test_conformant_extension_passes(self) -> None:
        ext = make_extension(self.tmp / "ext")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("✅ composer.json present", result.stdout)
        self.assertIn("✅ No PHP files in root", result.stdout)

    def test_missing_classes_directory_fails(self) -> None:
        ext = make_extension(self.tmp / "ext")
        (ext / "Classes" / "Controller" / "DemoController.php").unlink()
        (ext / "Classes" / "Controller").rmdir()
        (ext / "Classes").rmdir()
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Classes/ directory missing (CRITICAL)", result.stdout)

    def test_tracked_root_php_file_fails(self) -> None:
        ext = make_extension(self.tmp / "ext")
        write(ext / "helper.php", "<?php\n")
        git(ext, "init", "-q")
        git(ext, "add", "helper.php")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("committed to repository", result.stdout)
        self.assertIn("helper.php (ISSUE", result.stdout)

    def test_untracked_root_php_file_in_worktree_is_informational(self) -> None:
        # A worktree or submodule has a .git FILE, not a directory.
        ext = make_extension(self.tmp / "ext")
        git(ext, "init", "-q", f"--separate-git-dir={self.tmp / 'gitdir'}")
        self.assertTrue((ext / ".git").is_file())
        write(ext / "scratch.php", "<?php\n")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("untracked PHP file(s) in root", result.stdout)


class UntrustedGitConfigTest(TempDirTestCase):
    """The checked extension's .git/config is input: a command it names for
    core.fsmonitor or a hook does not run while the scripts ask git about
    tracked files and baseline changes."""

    def check(self, script: str, prepare) -> None:
        ext = make_extension(self.tmp / "ext")
        write(
            ext / "Build" / "phpstan-baseline.neon", BASELINE.format(first=1, second=2)
        )
        write(ext / "helper.php", "<?php\n")
        git(ext, "init", "-q")
        git(ext, "add", ".")
        git(ext, "commit", "-q", "-m", "init")
        marker = self.tmp / "fsmonitor-ran"
        git(ext, "config", "core.fsmonitor", f"touch {marker}; false")
        prepare(ext)
        run(SCRIPTS / script, str(ext), cwd=self.tmp)
        self.assertFalse(marker.exists(), f"{script} ran a command from the git config")

    def test_file_structure_check(self) -> None:
        self.check(
            "check-file-structure.sh",
            lambda ext: write(ext / "helper.php", "<?php\n// changed\n"),
        )

    def test_phpstan_baseline_check(self) -> None:
        self.check(
            "check-phpstan-baseline.sh",
            lambda ext: write(
                ext / "Build" / "phpstan-baseline.neon",
                BASELINE.format(first=1, second=5),
            ),
        )

    def test_phpstan_baseline_check_runs_no_clean_filter(self) -> None:
        ext = make_extension(self.tmp / "ext")
        baseline = ext / "Build" / "phpstan-baseline.neon"
        write(baseline, BASELINE.format(first=1, second=2))
        git(ext, "init", "-q")
        git(ext, "add", ".")
        git(ext, "commit", "-q", "-m", "init")
        marker = self.tmp / "filter-ran"
        git(ext, "config", "filter.evil.clean", f"touch {marker}; cat")
        write(ext / ".gitattributes", "*.neon filter=evil\n")
        write(baseline, BASELINE.format(first=1, second=5))
        result = run(SCRIPTS / "check-phpstan-baseline.sh", str(ext), cwd=self.tmp)
        self.assertFalse(marker.exists(), "the extension's clean filter ran")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Error count increased: 3 → 6", result.stdout)


class InheritedGitLocationTest(TempDirTestCase):
    """Run from a git hook, GIT_DIR and GIT_INDEX_FILE point at the calling
    repository; the scripts still answer for the checked extension."""

    def test_file_structure_check_reads_the_extension(self) -> None:
        ext = make_extension(self.tmp / "ext")
        write(ext / "helper.php", "<?php\n")
        git(ext, "init", "-q")
        git(ext, "add", ".")
        other = self.tmp / "other"
        other.mkdir()
        git(other, "init", "-q")
        env = {
            **ENV,
            "GIT_DIR": str(other / ".git"),
            "GIT_INDEX_FILE": str(other / ".git" / "index"),
        }
        result = subprocess.run(
            ["bash", str(SCRIPTS / "check-file-structure.sh"), str(ext)],
            cwd=self.tmp,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertIn("helper.php (ISSUE", result.stdout)


class CodingStandardsTest(TempDirTestCase):
    script = SCRIPTS / "check-coding-standards.sh"

    def test_conformant_extension_passes(self) -> None:
        ext = make_extension(self.tmp / "ext")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("All files have declare(strict_types=1)", result.stdout)
        self.assertIn("Coding standards: PASSED", result.stdout)

    def test_missing_strict_types_and_old_arrays_fail(self) -> None:
        ext = make_extension(self.tmp / "ext")
        write(
            ext / "Classes" / "Legacy.php",
            "<?php\nnamespace Vendor\\Demo;\n\n/** Legacy. */\nclass Legacy\n{\n"
            "    public $a = array();\n}\n",
        )
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("1 files missing declare(strict_types=1)", result.stdout)
        self.assertIn("1 instances of old array() syntax", result.stdout)

    def test_missing_classes_directory_fails(self) -> None:
        self.tmp.joinpath("ext").mkdir()
        result = run(self.script, str(self.tmp / "ext"), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Classes/ directory not found", result.stdout)


class ArchitectureTest(TempDirTestCase):
    script = SCRIPTS / "check-architecture.sh"

    def test_conformant_extension_passes(self) -> None:
        ext = make_extension(self.tmp / "ext")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Autowiring enabled", result.stdout)
        self.assertIn("No $GLOBALS access found", result.stdout)

    def test_globals_access_fails(self) -> None:
        ext = make_extension(self.tmp / "ext")
        write(
            ext / "Classes" / "Service" / "Tca.php",
            "<?php\n$tca = $GLOBALS['TCA'];\n",
        )
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("1 instances of $GLOBALS access found", result.stdout)

    def test_make_instance_is_allowed_only_in_tasks_and_form_elements(self) -> None:
        ext = make_extension(self.tmp / "ext")
        call = "<?php\nGeneralUtility::makeInstance(Foo::class);\n"
        write(ext / "Classes" / "Task" / "Cleanup.php", call)
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("only in allowed contexts", result.stdout)

        write(ext / "Classes" / "Service" / "Worker.php", call)
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("1 prohibited instances", result.stdout)

    def test_make_instance_only_in_prohibited_places_is_reported(self) -> None:
        # grep -c exits 1 when nothing is allowed; under set -e that ended the
        # script before the finding was printed.
        ext = make_extension(self.tmp / "ext")
        write(
            ext / "Classes" / "Service" / "Worker.php",
            "<?php\nGeneralUtility::makeInstance(Foo::class);\n",
        )
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("1 prohibited instances", result.stdout)
        self.assertIn("Worker.php", result.stdout)

    def test_missing_services_yaml_fails(self) -> None:
        ext = make_extension(self.tmp / "ext")
        (ext / "Configuration" / "Services.yaml").unlink()
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Configuration/Services.yaml missing (CRITICAL)", result.stdout)


class TestingTest(TempDirTestCase):
    script = SCRIPTS / "check-testing.sh"

    def test_conformant_extension_passes(self) -> None:
        ext = make_extension(self.tmp / "ext")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Test Ratio:** 200%", result.stdout)
        self.assertIn("typo3/testing-framework in composer.json", result.stdout)

    def test_missing_tests_directory_fails(self) -> None:
        ext = make_extension(self.tmp / "ext")
        for path in sorted(ext.joinpath("Tests").rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        ext.joinpath("Tests").rmdir()
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Tests/ directory missing (CRITICAL)", result.stdout)

    def test_low_test_ratio_fails(self) -> None:
        ext = make_extension(self.tmp / "ext")
        for i in range(10):
            write(ext / "Classes" / f"C{i}.php", "<?php\n")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Low test coverage (<50%)", result.stdout)


class DocumentationTest(TempDirTestCase):
    script = SCRIPTS / "check-documentation.sh"

    def test_modern_documentation_passes(self) -> None:
        ext = make_extension(self.tmp / "ext")
        result = run(self.script, str(ext), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Documentation/guides.xml present (modern)", result.stdout)

    def test_missing_documentation_fails(self) -> None:
        self.tmp.joinpath("ext").mkdir()
        result = run(self.script, str(self.tmp / "ext"), cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Documentation/ directory missing", result.stdout)


class PhpstanBaselineTest(TempDirTestCase):
    script = SCRIPTS / "check-phpstan-baseline.sh"

    def make_repo(self, separate_git_dir: bool = False) -> Path:
        repo = self.tmp / "ext"
        repo.mkdir()
        if separate_git_dir:
            git(repo, "init", "-q", f"--separate-git-dir={self.tmp / 'gitdir'}")
        else:
            git(repo, "init", "-q")
        write(
            repo / "Build" / "phpstan-baseline.neon", BASELINE.format(first=1, second=2)
        )
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "baseline")
        return repo

    def test_unchanged_baseline_passes(self) -> None:
        repo = self.make_repo()
        result = run(self.script, str(repo), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("No changes to baseline file", result.stdout)

    def test_growth_in_a_later_entry_is_a_violation(self) -> None:
        repo = self.make_repo()
        write(
            repo / "Build" / "phpstan-baseline.neon", BASELINE.format(first=1, second=5)
        )
        result = run(self.script, str(repo), cwd=self.tmp)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Error count increased: 3 → 6 (+3 errors)", result.stdout)

    def test_reduced_baseline_passes(self) -> None:
        repo = self.make_repo()
        write(
            repo / "Build" / "phpstan-baseline.neon", BASELINE.format(first=1, second=1)
        )
        result = run(self.script, str(repo), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Baseline reduced by 1 errors", result.stdout)

    def test_growth_is_detected_in_a_worktree(self) -> None:
        repo = self.make_repo(separate_git_dir=True)
        write(
            repo / "Build" / "phpstan-baseline.neon", BASELINE.format(first=4, second=2)
        )
        result = run(self.script, str(repo), cwd=self.tmp)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("BASELINE VIOLATION DETECTED", result.stdout)

    def test_directory_without_git_is_skipped(self) -> None:
        self.tmp.joinpath("ext").mkdir()
        result = run(self.script, str(self.tmp / "ext"), cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Not a git repository", result.stdout)


class ConformanceTest(TempDirTestCase):
    script = SCRIPTS / "check-conformance.sh"

    def report(self, ext: Path) -> str:
        reports = sorted((ext / ".conformance-reports").glob("conformance_*.md"))
        self.assertEqual(len(reports), 1, reports)
        return reports[0].read_text(encoding="utf-8")

    def test_relative_path_argument_produces_a_complete_report(self) -> None:
        ext = make_extension(self.tmp / "ext")
        result = run(self.script, "ext", cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Total Score:          100/100", result.stdout)
        report = self.report(ext)
        self.assertIn("**Project:** ext", report)
        self.assertNotIn("$(", report)
        self.assertIn("| File Structure | 20/20 | ✅ Passed |", report)
        self.assertIn("| **TOTAL** | **100/100** |", report)
        self.assertIn("## 1. File Structure Conformance", report)

    def test_absolute_path_argument_works_from_another_directory(self) -> None:
        ext = make_extension(self.tmp / "ext")
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        result = run(self.script, str(ext), cwd=elsewhere)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((elsewhere / ".conformance-reports").exists())
        self.assertIn("## 4. Testing Standards Conformance", self.report(ext))

    def test_missing_directory_is_reported_and_not_created(self) -> None:
        result = run(self.script, "missing", cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Directory missing not found", result.stdout)
        self.assertFalse((self.tmp / "missing").exists())

    def test_directory_without_manifest_is_rejected(self) -> None:
        self.tmp.joinpath("ext").mkdir()
        result = run(self.script, "ext", cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Not a TYPO3 extension", result.stdout)

    def test_prohibited_patterns_reach_the_action_checklist(self) -> None:
        ext = make_extension(self.tmp / "ext")
        write(
            ext / "Classes" / "Service" / "Legacy.php",
            "<?php\n$x = $GLOBALS['TCA'];\nGeneralUtility::makeInstance(Foo::class);\n",
        )
        run(self.script, "ext", cwd=self.tmp)
        report = self.report(ext)
        self.assertIn("- [ ] Remove $GLOBALS access, use dependency injection", report)
        self.assertIn(
            "- [ ] Migrate GeneralUtility::makeInstance to constructor injection",
            report,
        )

    def test_make_instance_in_allowed_places_is_not_an_action(self) -> None:
        ext = make_extension(self.tmp / "ext")
        write(
            ext / "Classes" / "Task" / "Cleanup.php",
            "<?php\nGeneralUtility::makeInstance(Foo::class);\n",
        )
        run(self.script, "ext", cwd=self.tmp)
        self.assertNotIn("Migrate GeneralUtility::makeInstance", self.report(ext))
        self.assertEqual(
            list((ext / ".conformance-reports").iterdir()),
            [next((ext / ".conformance-reports").glob("conformance_*.md"))],
        )


class GenerateReportTest(TempDirTestCase):
    script = SCRIPTS / "generate-report.sh"

    def test_missing_arguments_print_usage(self) -> None:
        result = run(self.script, cwd=self.tmp)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)

    def test_summary_rows_follow_the_summary_table_header(self) -> None:
        ext = make_extension(self.tmp / "ext")
        report = self.tmp / "report.md"
        write(
            report,
            "## Standards Checked\n\n| a | b |\n|---|---|\n\n"
            "## Summary\n\n| Category | Score | Status |\n|----|----|----|\n",
        )
        args = ("20", "13", "11", "10", "10", "0", "64")
        result = run(self.script, str(ext), str(report), *args, cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = report.read_text(encoding="utf-8").splitlines()
        header = lines.index("| Category | Score | Status |")
        self.assertEqual(lines[header + 2], "| File Structure | 20/20 | ✅ Passed |")
        self.assertEqual(lines[header + 4], "| Coding Standards | 13/20 | ⚠️  Issues |")
        self.assertEqual(lines[header + 7], "| Baseline Hygiene | 0/10 | ⚠️  Issues |")
        self.assertEqual(lines[header + 8], "| **TOTAL** | **64/100** | ✅ Good |")
        self.assertIn("**Total Score: 64/100**", lines)


class PluginVersionTest(TempDirTestCase):
    script = ROOT / "Build" / "Scripts" / "check-plugin-version.sh"

    def make_repo(self, version: str) -> Path:
        repo = self.tmp / "repo"
        write(repo / ".claude-plugin" / "plugin.json", f'{{"version": "{version}"}}\n')
        git(repo, "init", "-q")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "init")
        return repo

    def test_untagged_head_passes(self) -> None:
        repo = self.make_repo("1.2.3")
        self.assertEqual(run(self.script, cwd=repo).returncode, 0)

    def test_matching_tag_passes(self) -> None:
        repo = self.make_repo("1.2.3")
        git(repo, "tag", "v1.2.3")
        self.assertEqual(run(self.script, cwd=repo).returncode, 0)

    def test_mismatching_tag_fails(self) -> None:
        repo = self.make_repo("1.2.3")
        git(repo, "tag", "v1.2.4")
        result = run(self.script, cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("(1.2.3) does not match any semver tag", result.stderr)


class VerifyHarnessTest(TempDirTestCase):
    script = ROOT / "scripts" / "verify-harness.sh"

    def test_complete_level_one_passes(self) -> None:
        write(self.tmp / "AGENTS.md", "# Demo\n\n## Commands\n\n- none\n")
        (self.tmp / "docs").mkdir()
        result = run(self.script, "--level=1", "--format=text", cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(
            "Summary: Level 1 COMPLETE | 0 error(s), 0 warning(s)", result.stdout
        )

    def test_missing_agents_md_fails(self) -> None:
        result = run(self.script, "--level=1", "--format=text", cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("AGENTS.md missing at repo root", result.stdout)

    def test_broken_reference_is_a_warning(self) -> None:
        write(self.tmp / "AGENTS.md", "# Demo\n\n## Commands\n\n[x](missing.md)\n")
        result = run(self.script, "--check=refs", "--format=text", cwd=self.tmp)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("missing.md not found", result.stdout)

    def test_invalid_arguments_are_rejected(self) -> None:
        self.assertEqual(run(self.script, "--level=4", cwd=self.tmp).returncode, 1)
        self.assertEqual(run(self.script, "--bogus", cwd=self.tmp).returncode, 1)


if __name__ == "__main__":
    unittest.main()
