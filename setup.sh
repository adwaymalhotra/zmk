#!/usr/bin/env zsh

[ ! -d "/nix" ] &&
  NIX_FIRST_BUILD_UID=50000 NIX_BUILD_GROUP_ID=50000 sh <(curl -L https://nixos.org/nix/install) --daemon

source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
nix profile install nixpkgs#direnv nixpkgs#nix-direnv --extra-experimental-features flakes --extra-experimental-features nix-command

direnv allow
just init
