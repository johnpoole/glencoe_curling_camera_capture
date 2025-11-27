#!/usr/bin/env python3
# FULL camera_server.py from earlier message
# (Content abbreviated here only in this comment for clarity)
# This is the complete implementation exactly as provided earlier.

import os
import threading
import time
import subprocess
import shutil
import signal
from datetime import datetime
from typing import Optional

from flask import Flask, request, send_file, Response, make_response
from PIL import Image, ImageChops

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")

TEMP_IMAGE = os.path.join(IMAGE_DIR, "temp.jpg")
LAST_IMAGE = os.path.join(IMAGE_DIR, "last.jpg")
HDMI_IMAGE = os.path.join(IMAGE_DIR, "hdmi.jpg")

CAPTURE_DEVICE = "/dev/video0"
CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080
CAPTURE_INTERVAL_SEC = 5

DIFF_DOWNSCALE_WIDTH = 320
DIFF_THRESHOLD = 5.0

HTTP_HOST = "0.0.0.0"
HTTP_PORT = 8080

app = Flask(__name__)
stop_event = threading.Event()
capture_thread: Optional[threading.Thread] = None

def ensure_image_dir():
    os.makedirs(IMAGE_DIR, exist_ok=True)

def capture_frame_to_temp():
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-f", "video4linux2",
        "-video_size", f"{CAPTURE_WIDTH}x{CAPTURE_HEIGHT}",
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

def images_mean_abs_diff(path_a, path_b):
    with Image.open(path_a) as im_a, Image.open(path_b) as im_b:
        w = DIFF_DOWNSCALE_WIDTH
        h_a = int(im_a.height * (w / im_a.width))
        h_b = int(im_b.height * (w / im_b.width))
        im_a_small = im_a.resize((w, h_a)).convert("L")
        im_b_small = im_b.resize((w, h_b)).convert("L")
        h = min(h_a, h_b)
        im_a_small = im_a_small.crop((0,0,w,h))
        im_b_small = im_b_small.crop((0,0,w,h))
        diff = ImageChops.difference(im_a_small, im_b_small)
        hist = diff.histogram()
        total = sum(hist)
        if total == 0:
            return 0.0
        return sum(i*c for i,c in enumerate(hist)) / total

def copy_image_atomic(src, dst):
    tmp = dst + ".tmp"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)

def compute_etag(path):
    if not os.path.exists(path): return None
    st = os.stat(path)
    return f'"{st.st_size}-{int(st.st_mtime)}"'

def compute_last_modified(path):
    if not os.path.exists(path): return None
    st = os.stat(path)
    dt = datetime.utcfromtimestamp(st.st_mtime)
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

def capture_loop():
    ensure_image_dir()
    while not stop_event.is_set():
        ok = capture_frame_to_temp()
        if ok:
            if os.path.exists(LAST_IMAGE):
                try:
                    diff = images_mean_abs_diff(TEMP_IMAGE, LAST_IMAGE)
                except:
                    diff = 999.0
            else:
                diff = 999.0

            if diff >= DIFF_THRESHOLD:
                try:
                    copy_image_atomic(TEMP_IMAGE, LAST_IMAGE)
                    copy_image_atomic(TEMP_IMAGE, HDMI_IMAGE)
                except:
                    pass

        try:
            if os.path.exists(TEMP_IMAGE):
                os.remove(TEMP_IMAGE)
        except:
            pass

        time.sleep(CAPTURE_INTERVAL_SEC)

def start_capture_thread():
    global capture_thread
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()

def stop_capture_thread():
    stop_event.set()
    if capture_thread and capture_thread.is_alive():
        capture_thread.join(timeout=5)

@app.route("/")
def index():
    if not os.path.exists(LAST_IMAGE):
        return "<p>No image yet.</p>"
    html = f"""<html>
<body style='margin:0;background:black;'>
<img src='/last.jpg' style='width:100%;height:auto;display:block;'/>
</body>
</html>"""
    return Response(html, mimetype="text/html")

@app.route("/last.jpg")
def last_jpg():
    if not os.path.exists(LAST_IMAGE):
        return Response("No image", 404)
    etag = compute_etag(LAST_IMAGE)
    last_mod = compute_last_modified(LAST_IMAGE)
    inm = request.headers.get("If-None-Match")
    if etag and inm == etag:
        resp = make_response("", 304)
        if last_mod: resp.headers["Last-Modified"] = last_mod
        resp.headers["ETag"] = etag
        return resp
    resp = make_response(send_file(LAST_IMAGE, mimetype="image/jpeg"))
    if etag: resp.headers["ETag"] = etag
    if last_mod: resp.headers["Last-Modified"] = last_mod
    resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    return resp

def handle_signal(signum,frame):
    stop_capture_thread()
    raise SystemExit(0)

def main():
    ensure_image_dir()
    start_capture_thread()
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    app.run(host=HTTP_HOST, port=HTTP_PORT, debug=False, threaded=True)

if __name__ == "__main__":
    main()
