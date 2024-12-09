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

zephyr_sdk_version="0.16.3"
zephyr_sdk_name="zephyr-sdk-${zephyr_sdk_version}"
if [ ! -d "$HOME/.local/lib/${zephyr_sdk_name}" ]; then
  cd /tmp
  wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${zephyr_sdk_version}/${zephyr_sdk_name}_linux-x86_64.tar.xz
  wget -O - https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${zephyr_sdk_version}/sha256.sum | shasum --check --ignore-missing

  tar xvf ${zephyr_sdk_name}_linux-x86_64.tar.xz
  mv ${zephyr_sdk_name} $HOME/.local/lib/${zephyr_sdk_name}
  cd $HOME/.local/lib/${zephyr_sdk_name}
  ./setup.sh

  sudo cp sysroots/x86_64-pokysdk-linux/usr/share/openocd/contrib/60-openocd.rules /etc/udev/rules.d
  sudo udevadm control --reload
fi

cd $start_dir
