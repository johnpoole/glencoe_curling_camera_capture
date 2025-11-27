# Setup Guide: Raspberry Pi 3B – Glencoe Curling Camera Capture

## Required Hardware

- Raspberry Pi 3B
- USB UVC camera
- HDMI display
- 16 GB SD card or larger
- Network

## OS Image

Use **Raspberry Pi OS Lite (64-bit)** via Raspberry Pi Imager:

- `Raspberry Pi OS (other)` → `Raspberry Pi OS Lite (64-bit)`

If you already have Pi OS Lite 64-bit installed, you do **not** need to reflash.

## First Boot

1. Boot the Pi.
2. Complete the basic setup (locale, timezone, password).
3. Update packages:

```bash
sudo apt update
sudo apt upgrade -y
```

## Install Dependencies

```bash
sudo apt install -y git python3 python3-pip ffmpeg python3-pygame
```

## Clone the Repository

```bash
cd /home/pi
git clone <YOUR_REMOTE>/glencoe_curling_camera_capture.git
cd glencoe_curling_camera_capture
```

## Python Requirements

```bash
python3 -m pip install --break-system-packages -r requirements.txt
```

## Optional Test

```bash
python3 src/camera_server.py
```

## Install systemd Services

```bash
sudo cp systemd/camera_server.service systemd/framebuffer_display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera_server.service framebuffer_display.service
sudo systemctl start camera_server.service framebuffer_display.service
```

## Verify

```bash
sudo systemctl status camera_server.service --no-pager
sudo systemctl status framebuffer_display.service --no-pager
ls -l images
```
