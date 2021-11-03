## Docker images (Not maintenance)

### Usage

Choose your architecture (such as `aarch64`)

```plain
$ cd aarch64
$ sudo docker build . -t repobuildbase
$ cd ..
$ sudo docker build . -t repobuild
```

Or you can use `onekey.sh` to build it.

Then, start image

```plain
$ sudo docker run -it --rm --env-file docker.env repobuild
```
