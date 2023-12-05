#!/bin/bash

set -Eeuo pipefail
sudo pacman -Sy

cd /home/build

if [ -f ./hook-run.sh ]; then
   . ./hook-run.sh
fi

if [ ! -d repos ]; then
  git clone --depth=3 $1 repos


  pushd repos
  git checkout "$CHECKOUT_BRANCH"
  git fetch --recurse-submodules -j2
  git submodule update --init
  popd
fi

export DOCKER_SETUP_SCRIPT=1


if [ $UID -eq 0 ]; then
    chown -R build:build repos

    echo "$TARGET_HOSTS" | base64 -d >> /etc/hosts
else
    echo "$TARGET_HOSTS" | base64 -d | sudo tee -a /etc/hosts >/dev/null
fi

pushd repos
if [ $UID -eq 0 ]; then

    su -c "echo $GPG_PRIV_KEY | base64 -d | gpg --import" build

    su -c './utils/pkgbuild_bootstrap' build

else

    echo $GPG_PRIV_KEY | base64 -d | gpg --import

    ./utils/pkgbuild_bootstrap

fi

popd

