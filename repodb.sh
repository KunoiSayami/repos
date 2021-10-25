#!/bin/bash

# end up when failed
set -Eeuo pipefail

# clean up when exit
trap cleanup SIGINT SIGTERM ERR EXIT
cleanup() {
	trap - SIGINT SIGTERM ERR EXIT
	unset ARCH
	unset PKGDEST
	unset REPO_DEST
	unset GPG_KEY
	unset PACKAGE_NAME
	unset LATEST
}

REPO_BASE_NAME="kunoisayami"
ARCH=$(uname -m)
PKGDEST="${PWD}/packages/$ARCH"
REPO_DEST="${PWD}/packages/$ARCH/$REPO_BASE_NAME.db.tar.xz"
GPG_KEY="4A0F0C8BC709ACA4341767FB243975C8DB9656B9"

while read PACKAGE_NAME; do
    #LATEST=$(ls -t "$PKGDEST/$PACKAGE_NAME"* | grep -v ".sig" | head -n 1 | cut -d' ' -f1)
    if [ -z $PACKAGE_NAME ]; then
        continue
    fi
    repo-add "$REPO_DEST" "$PACKAGENAME" -s -v -R -k $GPG_KEY
done
