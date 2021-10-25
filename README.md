KunoiSayami's Arch Linux Community Repository
====

### Usage

#### Add repo:

```
[kunoisayami]
Server = https://MASKED/$repo
```
to your `/etc/pacman.conf` .

#### Import PGP Keys:

```bash
curl -fL https://keys.openpgp.org/vks/v1/by-fingerprint/4A0F0C8BC709ACA4341767FB243975C8DB9656B9 | sudo pacman-key --add -
sudo pacman-key --finger 4A0F0C8BC709ACA4341767FB243975C8DB9656B9
sudo pacman-key --lsign-key 4A0F0C8BC709ACA4341767FB243975C8DB9656B9
```

### For developers:

Use commit message starts with `fix(repo)` will let CI/CD rebuild all packages.
