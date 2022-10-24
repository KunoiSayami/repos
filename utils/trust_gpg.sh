#!/bin/bash
gpg --list-keys --fingerprint | grep pub -A 1 | grep -Ev "pub|--" | tr -d ' ' \
        | awk 'BEGIN { FS = "\n" } ; { print $1":6:" } ' | gpg --import-ownertrust