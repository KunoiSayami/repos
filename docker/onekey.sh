#!/bin/bash

# end up when failed
set -Eeuo pipefail

if [ $# -eq 0 ] && [ -z "$1" ]; then
    echo "Please specify REMOTE SERVER ADDRESS"
    exit 1
fi

pushd "$(uname -m)" || ( echo "Can't find your architecture" && exit 1 )
    docker buildx build . -t repobuildbase
popd

if [ -v http_proxy ]; then
  docker buildx build --build-arg "REMOTE_ADDRESS=$1" --build-arg="http_proxy=$http_proxy" --build-arg="https_proxy=$http_proxy" . -t repobuild;
else
  docker buildx build --build-arg "REMOTE_ADDRESS=$1" . -t repobuild;
fi
