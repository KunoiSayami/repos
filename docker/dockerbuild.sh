#!/bin/bash

set -Eeuo pipefail
sudo pacman -Sy

cd /home/build
git clone --depth=3 https://github.com/kunoisayami/repos

pushd repos
git checkout $CHECKOUT_BRANCH
git fetch --recurse-submodules -j2
git submodule update --init
popd


if [ $UID -eq 0 ]; then
    chown -R build:build repos

    echo "$TARGET_HOSTS" | base64 -d >> /etc/hosts
else
    echo "$TARGET_HOSTS" | base64 -d | sudo tee -a /etc/hosts >/dev/null
fi

pushd repos
if [ $UID -eq 0 ]; then

    su -c "echo $GPG_PRIV_KEY | base64 -d | gpg --import" build

    su -c './utils/pkgbuild.sh' build

    su -e -c './utils/ci-upload.sh' build

else

    echo $GPG_PRIV_KEY | base64 -d | gpg --import

    ./utils/pkgbuild.sh

    ./utils/ci-upload.sh

fi

popd

