#!/bin/bash
PKGDEST="${PWD}/repo/packages"
SRCDEST="${PWD}/build"
pushd kunoisayami
for folder in */ ; do
    PACKAGE_NAME=$(printf $folder | sed 's/.$//')
    pushd "$folder"
    pervpkg=$(ls "../../repo/packages/$PACKAGE_NAME"*)
    SRCPKGDEST=$SRCDEST SRCDEST=$SRCDEST PKGDEST=$PKGDEST makepkg --clean
    if [ $? != 13 ] && [ -z "$pervpkg" ]; then
        rm $pervpkg
    fi
    #cp "$PACKAGE_NAME"* ../../../packages/
    popd
done
popd
unset PACKAGE_NAME
