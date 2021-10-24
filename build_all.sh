#!/bin/bash
ARCH=$(uname -m)
PKGDEST="${PWD}/packages/$ARCH"
SRCDEST="${PWD}/build"
CONFDEST="${PWD}/makepkg.conf"
REPO_DEST="${PWD}/packages/$ARCH/kunoisayami.db.tar.xz"
REPO_PENDING="${PWD}/packages/$ARCH/PENDING"
touch "$REPO_PENDING"
pushd kunoisayami
for folder in */ ; do
    PACKAGE_NAME=$(printf $folder | sed 's/.$//')
    pushd "$folder"
    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST MAKEPKG_CONF=$CONFDEST makepkg --clean --sign --key 4A0F0C8BC709ACA4341767FB243975C8DB9656B9
    if [ $? == 0 ]; then
        echo "$PACKAGE_NAME" >> "$REPO_PENDING"
    fi
    #cp "$PACKAGE_NAME"* ../../../packages/
    popd
done
popd
while read PACKAGE_NAME; do
    LATEST=$(ls -t "$PKGDEST/$PACKAGE_NAME"* | grep -v ".sig" | head -n 1 | cut -d' ' -f1)
    repo-add "$REPO_DEST" "$LATEST" -s -v -R
done < "$REPO_PENDING"
echo $(date +%s) > "$PKGDEST/LASTBUILD"
unset PACKAGE_NAME
unset PKGDEST
unset SRCDEST
unset CONFDEST
unset REPO_DEST
rm -rf "$REPO_PENDING"
unset REPO_PENDING
