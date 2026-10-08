#!/usr/bin/env bash
# One-shot setup on a Raspberry Pi OS (Bookworm) station.  Run as the 'pi' user.
set -euo pipefail
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev chrony gpsd pps-tools rtklib  # rtklib gives convbin for RINEX
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -e ".[hardware,plots]"
sudo cp deploy/greylock-acquire.service deploy/greylock-serve.service /etc/systemd/system/
sudo cp deploy/greylock.cron /etc/cron.d/greylock
sudo cp deploy/chrony.conf /etc/chrony/chrony.conf
sudo systemctl daemon-reload
sudo systemctl enable chrony greylock-acquire greylock-serve
echo "edit station.toml (site, clock, serial ports), then: greylock doctor station.toml --live, then: sudo systemctl start greylock-acquire greylock-serve"
