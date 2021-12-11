#!/bin/bash

# no makepkg version
# https://github.com/archlinuxcn/repo/blob/master/parse-pkgbuild

pushd $(dirname $@) > /dev/null
makepkg --printsrcinfo
popd > /dev/null
