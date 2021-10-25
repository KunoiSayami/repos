#!/bin/bash

ARCH=$(uname -m)
PKGBUILD_DIRECTORY_BASE="repo"
PKGDEST="${PWD}/packages/$ARCH"
SRCDEST="${PWD}/build"
CONFDEST="${PWD}/makepkg.d/makepkg.$ARCH.conf"
REPO_PENDING="${PWD}/packages/$ARCH/PENDING"
REPO_DIFF="${PWD}/packages/$ARCH/DIFF"

trap 'rm -f "$TMPCONF"' EXIT
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

if [ $# -gt 0 ] && [ "$1" = "--all" ]; then
    ls $PKGBUILD_DIRECTORY_BASE > "$REPO_DIFF"
else
    get_diff_list
fi

pushd $PKGBUILD_DIRECTORY_BASE || ( echo "Error, can't switch to pkgbuild directory" && exit 1 )

while read PACKAGE_NAME ; do
    #PACKAGE_NAME=$(printf $folder | sed 's/.$//')
    pushd "$PACKAGE_NAME" || continue
    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF="$TMPCONF" makepkg --clean -s --asdeps --noconfirm --needed --noprogressbar
    if [ $? == 0 ]; then
        echo "$PACKAGE_NAME" >> "$REPO_PENDING"
    fi
    #cp "$PACKAGE_NAME"* ../../../packages/
    popd
done < "$REPO_DIFF"

popd

if [ -z "${BUILD_ONLY+x}" ]; then
    ./repodb.sh < "$REPO_PENDING"
else
    echo "Add package to database is skipped"
fi

date +%s > "$PKGDEST/LASTBUILD"

unset PACKAGE_NAME
unset PKGDEST
unset SRCDEST
unset CONFDEST
unset REPO_DEST
rm -rf "$REPO_PENDING"
rm -rf "$REPO_DIFF"
unset REPO_PENDING
unset REPO_DIFF
unset PKGBUILD_DIRECTORY_BASE
unset ARCH
unset REPO_BASE_NAME
