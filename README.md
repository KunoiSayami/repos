KunoiSayami's Arch Linux Community Repository
====

### Usage

#### Add repo:

```
[kunoisayami]
Server = https://MASKED/$arch
```
to your `/etc/pacman.conf` .

#### Import PGP Keys:

```bash
curl -fL https://keys.openpgp.org/vks/v1/by-fingerprint/4A0F0C8BC709ACA4341767FB243975C8DB9656B9 | sudo pacman-key --add -
sudo pacman-key --finger 4A0F0C8BC709ACA4341767FB243975C8DB9656B9
sudo pacman-key --lsign-key 4A0F0C8BC709ACA4341767FB243975C8DB9656B9
```

### For developers:

GitLab CI script is currently not under maintenance.

Dockerfile has been moved to utils directory.

You need to open a pull request for every add package request.

## License

_Except file under `repo` folder, this folder use [UNLICENSE](repo/UNLICENSE)_

[![](https://www.gnu.org/graphics/agplv3-155x51.png)](https://www.gnu.org/licenses/agpl-3.0.txt)

Copyright (C) 2021-2023 KunoiSayami && CoelacanthusHex

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
