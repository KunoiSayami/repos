#!/bin/bash

# end up when failed
set -Eeuo pipefail

if [ $# -eq 0 ] && [ -z "$1" ]; then
    echo "Please specify REMOTE SERVER ADDRESS"
    exit 1
fi

pushd "$(uname -m)" || ( echo "Can't find your architecture" && exit 1 )
docker build . -t repobuildbase
popd
docker build --build-arg "REMOTE_ADDRESS=$1" . -t repobuild
