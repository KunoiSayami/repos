#!/bin/bash

# end up when failed
set -Eeo pipefail

# clean up when exit
trap cleanup SIGINT SIGTERM ERR EXIT
cleanup() {
	trap - SIGINT SIGTERM ERR EXIT
    unset SIGNING_ARG
    unset UNSUCCESSFUL
    unset SKIP_VERIFIED
	unset FOLDER_NAME
	unset PKGDEST
	unset SRCDEST
	unset CONFDEST
	unset REPO_DEST
	rm -f "$TMPCONF"
    if ! { [ $# -gt 0 ] && [ "$1" = "--diff" ]; }; then
	    rm -f "$REPO_DIFF"
    fi
    [ -r "$FAIL_REPOS" ] && rm -f "$FAIL_REPOS"
	unset TMPCONF
	unset REPO_PENDING
	unset REPO_DIFF
	unset PKGBUILD_DIRECTORY_BASE
	unset ARCH
}

function hook {
    if [ -r ../.hook/"$1" ]; then
        echo "Running $1 Hook script"
        ../.hook/"$1"
    fi
}

ARCH=$(uname -m)
PKGBUILD_DIRECTORY_BASE="repo"
FAIL_REPOS="${PWD}/failure_repos"
PKGDEST="${PWD}/packages/$ARCH"
SRCDEST="${PWD}/build"
CONFDEST="${PWD}/makepkg.d/makepkg.$ARCH.conf"
REPO_DIFF="${PWD}/packages/$ARCH/DIFF"
SKIP_VERIFIED=1
UNSUCCESSFUL=0
SIGNING_ARG="--nosign"

TMPCONF=$(mktemp -t makepkg.$ARCH.conf.XXXXXXXXXX) || exit 1
cat "${PWD}/makepkg.d/makepkg.base.conf" > "$TMPCONF"
cat "$CONFDEST" >> "$TMPCONF"

touch "$REPO_DIFF"

function get_diff_list {
    git diff --name-only HEAD^ | while read line; do
        if [[ $line =~ $PKGBUILD_DIRECTORY_BASE/\..+ ]] && [ "$line" != "$PKGBUILD_DIRECTORY_BASE/.verified_repos" ]; then
            echo "$line" | cut -d'/' -f3 >> "$REPO_DIFF"
        elif [[ $line =~ $PKGBUILD_DIRECTORY_BASE ]]; then
            echo "$line" | cut -d'/' -f2 >> "$REPO_DIFF"
        fi
    done
    cp "$REPO_DIFF"  "${REPO_DIFF}_tmp"
    sort -u "${REPO_DIFF}_tmp" > "$REPO_DIFF"
    rm -f "${REPO_DIFF}_tmp"
}

if [ $# -gt 0 ];then
    if [ "$1" = "--diff" ]; then
        get_diff_list
        exit 0
    elif [ "$1" = "--import-gpg" ]; then
        if [ -n "$CI_COMMIT_BRANCH" ] && [ -n "$CI_DEFAULT_BRANCH" ] && [[ "$CI_COMMIT_BRANCH" == "$CI_DEFAULT_BRANCH" ]]; then
            echo $GPG_PRIV_KEY | base64 -d | gpg --import
        else
            echo -e "\033[0;32mSkip import gpg key\033[0m"
        fi
        exit 0
    fi
fi

if [ "$EUID" -eq 0 ] ; then
    echo "\033[0;32mPlease run this script as non-root\033[0m"
    exit 3
fi

if [ $# -gt 0 ] && [ "$1" = "--all" ] || [ -n "$CI_COMMIT_TITLE" ] && [[ $CI_COMMIT_TITLE =~ fix\(repo\)|REBUILD ]]; then
    if [ -z "${FORCE_ALL+x}" ] || [ -n "$CI_COMMIT_TITLE" ] && [[ $CI_COMMIT_TITLE =~ REBUILD(\ |_)ALL ]]; then
        SKIP_VERIFIED=0
    fi
    ls $PKGBUILD_DIRECTORY_BASE > "$REPO_DIFF"
else
    get_diff_list
fi

if [ -n "$CI_COMMIT_BRANCH" ] && [ -n "$CI_DEFAULT_BRANCH" ] && [[ "$CI_COMMIT_BRANCH" == "$CI_DEFAULT_BRANCH" ]]; then
    SIGNING_ARG="--sign"
else
    echo -e "\033[0;32mSkip signing package\033[0m"
fi

pushd $PKGBUILD_DIRECTORY_BASE || ( echo -e "\033[0;31mError, can't switch to pkgbuild directory\033[0m" && exit 1 )

while read -r FOLDER_NAME ; do
    if [ ! -d "$FOLDER_NAME" ]; then
        echo -e "\033[0;32mSkip folder $FOLDER_NAME\033[0m"
        continue
    fi
    echo -e "\033[0;32mProcessing $FOLDER_NAME\033[0m"
    pushd "$FOLDER_NAME" || { echo -e "\033[1;33mWarning, can't chdir to $FOLDER_NAME, skipped\033[0m"; continue; }

    if [ -n "$CI_COMMIT_TITLE" ] && [[ $CI_COMMIT_TITLE =~ fix\(repo\)|REBUILD ]] && \
        [ $SKIP_VERIFIED -eq 1 ] && grep -Fxq "$FOLDER_NAME" "../.verified_repos"; then
        echo -e "\033[0;32mSkip folder $FOLDER_NAME (verified repository)\033[0m"
        popd
        continue
    fi

    # hook must run before other checker
    hook "$FOLDER_NAME"

    # Check PKGBUILD architecture
    if ! ( pcregrep -M 'arch=\([^\)]*\)' PKGBUILD | grep -E "$ARCH|any" >/dev/null ); then
        echo -e "\033[0;32mSkip folder $FOLDER_NAME (Architecture not match)\033[0m"
        popd
        continue
    fi

    if [ -n "$CI_COMMIT_TITLE" ] && [[ $CI_COMMIT_TITLE =~ fix\(repo\)|REBUILD ]] && \
        [ $SKIP_VERIFIED -eq 1 ] && grep -Fxq "$FOLDER_NAME" "../.verified_repos"; then
        echo -e "\033[0;32mSkip folder $FOLDER_NAME (verified repository)\033[0m"
        popd
        continue
    fi

    if [ -r ../.yaydeps/"$FOLDER_NAME" ]; then
        while read -r YAYDEP ; do
            if [ -d "../$YAYDEP" ]; then
                pushd "../$YAYDEP"
                hook "$YAYDEP"
                SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF="$TMPCONF" makepkg --clean -s -i $SIGNING_ARG --asdeps --noconfirm --needed --noprogressbar
                popd
            else
                yay -S --noconfirm --needed --asdeps "$YAYDEP"
            fi
        done < ../.yaydeps/"$FOLDER_NAME"
    fi

    if [ -r ../.gpg_keys/"$FOLDER_NAME" ]; then
        . ../.gpg_keys/"$FOLDER_NAME"
        # source: https://stackoverflow.com/a/53886735
        gpg --list-keys --fingerprint | grep pub -A 1 | grep -Ev "pub|--" | tr -d ' ' \
        | awk 'BEGIN { FS = "\n" } ; { print $1":6:" } ' | gpg --import-ownertrust
    fi

    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF="$TMPCONF" makepkg -s --clean $SIGNING_ARG --asdeps --noconfirm --needed --noprogressbar || {
        LAST_STATUS=$?;
        if [ $LAST_STATUS -eq 13 ]; then
            echo -e "\033[0;32mSkip folder that package already build $FOLDER_NAME\033[0m";
            continue
        fi
        echo "$FOLDER_NAME" >> "$FAIL_REPOS"
        echo -e "\033[0;31mSkip folder $FOLDER_NAME. Build fail: $LAST_STATUS\033[0m";
        UNSUCCESSFUL=1;
    }
    [ -d "$SRCDEST" ] && rm -r "$SRCDEST"
    popd
done < "$REPO_DIFF"

popd

date +%s > "$PKGDEST/LASTBUILD"

if [ $UNSUCCESSFUL -eq 1 ]; then
    [ -d "$SRCDEST" ] && rm -r "$SRCDEST"
    echo -e "\033[0;31mBuild failed repositories:\033[0m"
    cat "$FAIL_REPOS"
    if [ -n "$CI_DEFAULT_BRANCH" ] && [ -n "$CI_COMMIT_BRANCH" ] && [[ "$CI_COMMIT_BRANCH" == "$CI_DEFAULT_BRANCH" ]]; then
        touch .fail
        echo -e "\033[0;31mCreate fail flag because \$UNSUCCESSFUL set to 1\033[0m"
    else
        echo -e "\033[0;31mExit due makepkg failed\033[0m"
        exit 2
    fi
fi
