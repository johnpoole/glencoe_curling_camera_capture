# Setup Guide: Raspberry Pi 3B – Glencoe Curling Camera Capture

## Required Hardware
- Raspberry Pi 3B
- USB UVC camera
- HDMI display
- 16 GB SD card or larger
- Network

## OS Image
Use **Raspberry Pi OS with desktop (32-bit)** via Raspberry Pi Imager.

## First Boot
Complete wizard, update system.

## Install dependencies
sudo apt update
sudo apt install -y git python3 python3-pip ffmpeg feh

## Clone repo
cd /home/pi
git clone <YOUR_REMOTE>/glencoe_curling_camera_capture

## Python requirements
python3 -m pip install --break-system-packages -r requirements.txt

## Test server
python3 src/camera_server.py

## Install systemd units
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera_server.service hdmi_display.service
sudo systemctl start camera_server.service hdmi_display.service
