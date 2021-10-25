#!/bin/bash

# end up when failed
set -Eeuo pipefail

# clean up when exit
trap cleanup SIGINT SIGTERM ERR EXIT
cleanup() {
	trap - SIGINT SIGTERM ERR EXIT
	unset ARCH
	unset PKGDEST
}

ARCH=$(uname -m)
PKGDEST="${PWD}/packages/$ARCH"

curl -d "token=$UPLOAD_TOKEN&action=REQUIRE_CLEAN" -fsSL "$REMOTE_PATH"

pushd $PKGDEST

for file in *.pkg*; do
	echo "Start upload package $file ..."
    curl -F "file=@$file" -F "token=$UPLOAD_TOKEN" -fsSL "$REMOTE_PATH"
	echo "Stop upload package $file"
done

popd

curl -d "token=$UPLOAD_TOKEN&action=UPLOADED" -fsSL "$REMOTE_PATH"

