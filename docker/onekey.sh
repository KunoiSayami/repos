#!/bin/bash

# end up when failed
set -Eeuo pipefail

pushd "$(uname -m)" || ( echo "Can't find your architecture" && exit 0 )
docker build . -t repobuildbase
popd
docker build . -t repobuild