#!/bin/bash
# pi/setup.sh — First-time Pi setup for LiveHaul
# Tested on Raspberry Pi OS Bookworm 64-bit

set -e

echo "=================================="
echo "  LiveHaul -- Pi Setup"
echo "=================================="

sudo apt-get update -qq
sudo apt-get install -y git curl docker.io docker-compose avahi-daemon

sudo usermod -aG docker "$USER"

sudo hostnamectl set-hostname livehaul
echo "Hostname set to 'livehaul' — accessible at http://livehaul.local"

sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

mkdir -p ~/livehaul-server/osrm/data
mkdir -p ~/livehaul-server/data

sudo cp "$(dirname "$0")/systemd/livehaul.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable livehaul

echo ""
echo "Setup complete!"
echo "1. Copy OSRM data: rsync -av osrm/data/ pi@livehaul.local:~/livehaul-server/osrm/data/"
echo "2. Start: cd ~/livehaul-server && docker-compose up -d"
echo "3. Check: http://livehaul.local:8000/health"
echo ""
echo "NOTE: Log out and back in for Docker group to take effect."
