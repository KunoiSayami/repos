#!/bin/bash
PKGDEST="${PWD}/repo/packages"
SRCDEST="${PWD}/build"
REPO_DEST="${PWD}/repo/kunoisayami.db.tar.xz"
REPO_PENDING="${PWD}/repo/PENDING"
touch "$REPO_PENDING"
pushd kunoisayami
for folder in */ ; do
    PACKAGE_NAME=$(printf $folder | sed 's/.$//')
    pushd "$folder"
    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST makepkg --clean
    if [ $? == 0 ]; then
        echo "$PACKAGE_NAME" >> "$REPO_PENDING"
    fi
    #cp "$PACKAGE_NAME"* ../../../packages/
    popd
done
popd
while read PACKAGE_NAME; do
    LATEST=$(ls -t "$PKGDEST/$PACKAGE_NAME"* | head -n 1 | cut -d' ' -f1)
    repo-add "$REPO_DEST" "$LATEST" -s -v -R
done < "$REPO_PENDING"
unset PACKAGE_NAME
unset PKGDEST
unset SRCDEST
unset REPO_DEST
rm -rf "$REPO_PENDING"
unset REPO_PENDING
