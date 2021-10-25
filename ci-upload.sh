#!/bin/bash

ARCH=$(uname -m)
PKGDEST="${PWD}/packages/$ARCH"

curl -d "token=$UPLOAD_TOKEN&action=REQUIRE_CLEAN" -fsSL "$REMOTE_PATH"

pushd $PKGDEST

for file in *.pkg*; do
    curl -F "file=@$file" -F "token=$UPLOAD_TOKEN" -fsSL "$REMOTE_PATH"
done

popd

curl -d "token=$UPLOAD_TOKEN&action=UPLOADED" -fsSL "$REMOTE_PATH"

unset ARCH
unset PKGDEST
