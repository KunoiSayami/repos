#!/bin/bash

set -Eeuo pipefail

cd /home/build
git clone --depth=3 https://github.com/kunoisayami/repos


if [ $UID -eq 0 ]; then
    chown -R build:build repos
    echo "$TARGET_HOSTS" | base64 -d >> /etc/hosts
else
    echo "$TARGET_HOSTS" | base64 -d | sudo tee -a /etc/hosts >/dev/null
fi

pushd repos
if [ $UID -eq 0 ]; then
    su -c "echo $GPG_PRIV_KEY | base64 -d | gpg --import" build

    pushd repo/pod2man
    su -c 'makepkg -i -s --noconfirm --needed' build
    popd

    su -c 'BUILD_ONLY="" ./pkgbuild.sh' build

    su -e -c './ci-upload.sh' build
else

    echo $GPG_PRIV_KEY | base64 -d | gpg --import

    pushd repo/pod2man
    makepkg -i -s --noconfirm --needed
    popd

    BUILD_ONLY='' ./pkgbuild.sh

    ./ci-upload.sh

fi

popd repos

