#!/bin/bash

# end up when failed
set -Eeuo pipefail

# clean up when exit
trap cleanup SIGINT SIGTERM ERR EXIT
cleanup() {
	trap - SIGINT SIGTERM ERR EXIT
	unset PACKAGE_NAME
	unset PKGDEST
	unset SRCDEST
	unset CONFDEST
	unset REPO_DEST
	rm -f "$TMPCONF"
	rm -f "$REPO_PENDING"
	rm -f "$REPO_DIFF"
	unset TMPCONF
	unset REPO_PENDING
	unset REPO_DIFF
	unset PKGBUILD_DIRECTORY_BASE
	unset ARCH
}

ARCH=$(uname -m)
PKGBUILD_DIRECTORY_BASE="repo"
PKGDEST="${PWD}/packages/$ARCH"
SRCDEST="${PWD}/build"
CONFDEST="${PWD}/makepkg.d/makepkg.$ARCH.conf"
REPO_PENDING="${PWD}/packages/$ARCH/PENDING"
REPO_DIFF="${PWD}/packages/$ARCH/DIFF"

TMPCONF=$(mktemp -t makepkg.$ARCH.conf.XXXXXXXXXX) || exit 1
cat "${PWD}/makepkg.d/makepkg.base.conf" > "$TMPCONF"
cat "$CONFDEST" >> "$TMPCONF"

touch "$REPO_DIFF"
touch "$REPO_PENDING"

function get_diff_list {
    git diff --name-only HEAD^ | while read line; do
        if [[ $line =~ $PKGBUILD_DIRECTORY_BASE ]]; then
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

if [ $# -gt 0 ] && [ "$1" = "--all" ] || [ -z "$CI_COMMIT_TITLE" ] && [[ $CI_COMMIT_TITLE =~ "fix(repo)" ]]; then
    ls $PKGBUILD_DIRECTORY_BASE > "$REPO_DIFF"
else
    get_diff_list
fi

pushd $PKGBUILD_DIRECTORY_BASE || ( echo "Error, can't switch to pkgbuild directory" && exit 1 )

while read PACKAGE_NAME ; do
    #PACKAGE_NAME=$(printf $folder | sed 's/.$//')
    pushd "$PACKAGE_NAME" || continue
    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF="$TMPCONF" makepkg --clean -s --asdeps --noconfirm --needed --noprogressbar
    echo "$PACKAGE_NAME" >> "$REPO_PENDING"
    popd
done < "$REPO_DIFF"

popd

if [ -z "${BUILD_ONLY+x}" ]; then
    ./repodb.sh < "$REPO_PENDING"
else
    echo "Add package to database is skipped"
fi

date +%s > "$PKGDEST/LASTBUILD"

