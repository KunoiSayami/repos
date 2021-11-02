#!/bin/bash

# end up when failed
set -Eeuo pipefail

# clean up when exit
trap cleanup SIGINT SIGTERM ERR EXIT
cleanup() {
	trap - SIGINT SIGTERM ERR EXIT
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
	unset TMPCONF
	unset REPO_PENDING
	unset REPO_DIFF
	unset PKGBUILD_DIRECTORY_BASE
	unset ARCH
}

function hook {
    if [ -r ../.hook/"$1" ]; then
        echo "Running $1 Hook script"
        . ../.hook/"$1"
    fi
}

ARCH=$(uname -m)
PKGBUILD_DIRECTORY_BASE="repo"
PKGDEST="${PWD}/packages/$ARCH"
SRCDEST="${PWD}/build"
CONFDEST="${PWD}/makepkg.d/makepkg.$ARCH.conf"
REPO_DIFF="${PWD}/packages/$ARCH/DIFF"
SKIP_VERIFIED=1

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
    sort "${REPO_DIFF}_tmp" | uniq -u > "$REPO_DIFF"
    rm -rf "${REPO_DIFF}_tmp"
}

if [ $# -gt 0 ] && [ "$1" = "--diff" ]; then
    get_diff_list
    exit 0
fi

if [ $# -gt 0 ] && [ "$1" = "--all" ] || [ -n "$CI_COMMIT_TITLE" ] && [[ $CI_COMMIT_TITLE =~ fix\(repo\)|REBUILD ]]; then
    if [ -z "${FORCE_ALL+x}" ] || [ -n "$CI_COMMIT_TITLE" ] && [[ $CI_COMMIT_TITLE =~ REBUILD(\ |_)ALL ]]; then
        SKIP_VERIFIED=0
    fi
    ls $PKGBUILD_DIRECTORY_BASE > "$REPO_DIFF"
else
    get_diff_list
fi

pushd $PKGBUILD_DIRECTORY_BASE || ( echo "Error, can't switch to pkgbuild directory" && exit 1 )

while read FOLDER_NAME ; do
    if [ ! -d "$FOLDER_NAME" ]; then
        continue
    fi
    pushd "$FOLDER_NAME" || continue
    # Check PKGBUILD architecture
    if ! ( pcregrep -M 'arch=\([^\)]*\)' PKGBUILD | grep -E "$ARCH|any" >/dev/null ); then
        popd
        continue
    fi

    if [ $SKIP_VERIFIED -eq 1 ] && grep -Fxq "$FOLDER_NAME" "../.verified_repos"; then
        popd
        continue
    fi

    if [ -r ../.yaydeps/"$FOLDER_NAME" ]; then
        while read YAYDEP ; do
            if [ -d "../$YAYDEP" ]; then
                pushd "../$YAYDEP"
                hook "$YAYDEP"
                SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF="$TMPCONF" makepkg --clean -si --asdeps --noconfirm --needed --noprogressbar
                popd
            else
                yay -S --noconfirm --needed --asdeps "$YAYDEP"
            fi
        done < ../.yaydeps/"$FOLDER_NAME"
    fi

    if [ -r ../.gpg_keys/"$FOLDER_NAME" ]; then
        . ../.gpg_keys/"$FOLDER_NAME"
    fi

    hook "$FOLDER_NAME"
    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF="$TMPCONF" makepkg --clean -s --asdeps --noconfirm --needed --noprogressbar || echo "Skip $FOLDER_NAME"
    popd
done < "$REPO_DIFF"

popd

if [ -z "${BUILD_ONLY+x}" ]; then
    echo "This option is depreacted, this script isn't process repository database now"
fi

date +%s > "$PKGDEST/LASTBUILD"

