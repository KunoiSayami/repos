KunoiSayami's Arch Linux Community Repository
====

### Usage

#### Add repo:

```
[kunoisayami]
Server = https://MASKED/repo
```
to your /etc/pacman.conf .

#### Import PGP Keys:

```bash
curl -fL https://keys.openpgp.org/vks/v1/by-fingerprint/43C24AB2392DFB61D7A5E4838B97E42C37978965 | sudo pacman-key --add -
sudo pacman-key --finger 43C24AB2392DFB61D7A5E4838B97E42C37978965
sudo pacman-key --lsign-key 43C24AB2392DFB61D7A5E4838B97E42C37978965
```
