#! /usr/bin/env bash
# Build APK file locally (the build is usually done in GHA when pushed to main)

if [[ -n $@ ]]; then
    cmd=$@
else
    cmd="--verbose android debug"
fi

sudo docker pull ghcr.io/kivy/buildozer:latest
sudo docker build --tag=kivy/buildozer "$PWD/buildozer"
mkdir -p .buildozer bin  # create dirs now so that they're user-owned
sudo docker run \
    --interactive \
    --tty \
    --rm \
    --volume "$HOME/.buildozer:/home/user/.buildozer" \
    --volume "$HOME/.gradle:/home/ubuntu/.gradle" \
    --volume "$PWD:/home/user/hostcwd" \
    kivy/buildozer $cmd
