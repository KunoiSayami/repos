#!/bin/bash

# end up when failed
set -Eeuo pipefail

if [ $# -eq 0 ]; then
    echo 'Should provide least one argument'
    exit 1
fi
ARCH=$(/usr/bin/uname -m)
/usr/bin/date +%s > "packages/$ARCH/LASTSYNC"
/usr/bin/rsync --partial -r --update --links --delete --exclude=.gitignore "packages/$ARCH" $1:/var/www/repo/
