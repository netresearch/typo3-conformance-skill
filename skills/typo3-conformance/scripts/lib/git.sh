# shellcheck shell=bash
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Netresearch DTT GmbH
#
# Git in the checked extension. Its .git/config is input like any other file
# and can name commands git runs: core.fsmonitor when git refreshes the index
# (git diff and git ls-files do) and hooks. project_git turns both off and
# skips the system config; callers add --no-ext-diff / --no-textconv where a
# diff driver could otherwise run. Inherited variables that point git at
# another repository or index (set when the checks run from a git hook) are
# removed, so git answers for the checked extension.

project_git() {
    env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_OBJECT_DIRECTORY \
        -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u GIT_COMMON_DIR -u GIT_NAMESPACE \
        GIT_CONFIG_NOSYSTEM=1 git -c core.fsmonitor=false -c core.hooksPath=/dev/null "$@"
}
