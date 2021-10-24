#!/bin/bash

REPO_BASE_NAME="kunoisayami"
ARCH=$(uname -m)
PKGBUILD_DIRECTORY_BASE="kunoisayami"
PKGDEST="${PWD}/packages/$ARCH"
SRCDEST="${PWD}/build"
REPO_DEST="${PWD}/packages/$ARCH/$REPO_BASE_NAME.db.tar.xz"
REPO_PENDING="${PWD}/packages/$ARCH/PENDING"
REPO_DIFF="${PWD}/packages/$ARCH/DIFF"

touch "$REPO_DIFF"
touch "$REPO_PENDING"

if [ $# -gt 0 ] &&  [ "$1" = "--all" ]; then
    ls $PKGBUILD_DIRECTORY_BASE > "$REPO_DIFF"
else
    git diff --name-only HEAD^ | while read line; do
        if [[ $line =~ $PKGBUILD_DIRECTORY_BASE ]]; then
            echo "$line" | cut -d'/' -f2 >> "$REPO_DIFF"
        fi
    done
    cp "$REPO_DIFF"  "${REPO_DIFF}_tmp"
    sort "${REPO_DIFF}_tmp" | uniq -u > "$REPO_DIFF"
    rm -rf "${REPO_DIFF}_tmp"
fi

pushd $PKGBUILD_DIRECTORY_BASE || ( echo "Error, can't switch to pkgbuild directory" && exit 1 )

while read PACKAGE_NAME ; do
    #PACKAGE_NAME=$(printf $folder | sed 's/.$//')
    pushd "$PACKAGE_NAME" || continue
    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF=$CONFDEST makepkg --clean
    if [ $? == 0 ]; then
        echo "$PACKAGE_NAME" >> "$REPO_PENDING"
    fi
    #cp "$PACKAGE_NAME"* ../../../packages/
    popd
done < "$REPO_DIFF"

popd

while read PACKAGE_NAME; do
    LATEST=$(ls -t "$PKGDEST/$PACKAGE_NAME"* | grep -v ".sig" | head -n 1 | cut -d' ' -f1)
    repo-add "$REPO_DEST" "$LATEST" -s -v -R -k 4A0F0C8BC709ACA4341767FB243975C8DB9656B9
done < "$REPO_PENDING"

echo $(date +%s) > "$PKGDEST/LASTBUILD"

unset PACKAGE_NAME
unset PKGDEST
unset SRCDEST
unset REPO_DEST
rm -rf "$REPO_PENDING"
rm -rf "$REPO_DIFF"
unset REPO_PENDING
