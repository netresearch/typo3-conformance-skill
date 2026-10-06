# shellcheck shell=bash
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Netresearch DTT GmbH
#
# Git in the checked extension. Its .git/config is input like any other file
# and can name commands git runs: core.fsmonitor when git refreshes the index
# (git diff and git ls-files do) and hooks. project_git turns both off and
# skips the system config; callers add --no-ext-diff / --no-textconv where a
# diff driver could otherwise run.

project_git() {
    GIT_CONFIG_NOSYSTEM=1 command git -c core.fsmonitor=false -c core.hooksPath=/dev/null "$@"
}
