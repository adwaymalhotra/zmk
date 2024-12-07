#!/usr/bin/env bash
start_dir=$PWD
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate

pip install west

west init -l config
west update
west zephyr-export

pip install -r zephyr/scripts/requirements-base.txt

cd /tmp
wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.3/zephyr-sdk-0.16.3_linux-x86_64.tar.xz
wget -O - https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.3/sha256.sum | shasum --check --ignore-missing

tar xvf zephyr-sdk-0.16.3_linux-x86_64.tar.xz
mv zephyr-sdk-0.16.3 ~/.local/lib/zephyr-sdk-0.16.3
cd ~/.local/lib/zephyr-sdk-0.16.3
./setup.sh

sudo cp ~/.local/lib/zephyr-sdk-0.16.3/sysroots/x86_64-pokysdk-linux/usr/share/openocd/contrib/60-openocd.rules /etc/udev/rules.d
sudo udevadm control --reload

cd $start_dir
