#!/usr/bin/env python3
import os
import time
import threading
import subprocess
from flask import Flask, send_file

# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(BASE_DIR, "images")

LAST_IMAGE = os.path.join(IMAGE_DIR, "last.jpg")
HDMI_IMAGE = os.path.join(IMAGE_DIR, "hdmi.jpg")
TEMP_IMAGE = os.path.join(IMAGE_DIR, "temp.jpg")

CAPTURE_DEVICE = "/dev/video0"
CAPTURE_INTERVAL_SEC = 2   # Change as needed

stop_event = threading.Event()

# --------------------------------------------------------------------
# Image directory setup
# --------------------------------------------------------------------
def ensure_image_dir() -> None:
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR, exist_ok=True)

# --------------------------------------------------------------------
# Atomic file copy
# --------------------------------------------------------------------
def copy_image_atomic(src: str, dst: str) -> None:
    tmp = dst + ".tmp"
    try:
        if os.path.exists(tmp):
            os.remove(tmp)
    except Exception:
        pass
    subprocess.run(["cp", src, tmp], check=False)
    try:
        os.replace(tmp, dst)
    except Exception:
        pass

# --------------------------------------------------------------------
# Capture a *single* frame from the HDMI capture device
# NOTE: No forced resolution. ffmpeg negotiates automatically.
# --------------------------------------------------------------------
def capture_frame_to_temp() -> bool:
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-f", "video4linux2",
        "-i", CAPTURE_DEVICE,
        "-frames:v", "1",
        "-q:v", "4",
        "-y", TEMP_IMAGE,
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# --------------------------------------------------------------------
# Continuous capture loop
# --------------------------------------------------------------------
def capture_loop() -> None:
    ensure_image_dir()
    while not stop_event.is_set():
        ok = capture_frame_to_temp()
        if ok:
            try:
                copy_image_atomic(TEMP_IMAGE, LAST_IMAGE)
                copy_image_atomic(TEMP_IMAGE, HDMI_IMAGE)
            except Exception:
                pass

        # Clean up temp file
        try:
            if os.path.exists(TEMP_IMAGE):
                os.remove(TEMP_IMAGE)
        except Exception:
            pass

        time.sleep(CAPTURE_INTERVAL_SEC)

# --------------------------------------------------------------------
# Flask server
# --------------------------------------------------------------------
app = Flask(__name__)

@app.route("/")
def root() -> str:
    return "<h2>Glencoe Curling Camera Capture</h2><p>Use /last.jpg for the latest image.</p>"

@app.route("/last.jpg")
def last_jpg():
    return send_file(LAST_IMAGE, mimetype="image/jpeg")

@app.route("/hdmi.jpg")
def hdmi_jpg():
    return send_file(HDMI_IMAGE, mimetype="image/jpeg")

# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------
if __name__ == "__main__":
    t = threading.Thread(target=capture_loop, daemon=True)
    t.start()

    try:
        app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
    finally:
        stop_event.set()
        t.join()
