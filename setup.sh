#!/usr/bin/env bash

sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate

pip install west

west init -l config
west update

python3 -m venv zmk/.venv
source zmk/.venv/bin/activate

pip install west
west zephyr-export
pip install -r zephyr/scripts/requirements-base.txt
