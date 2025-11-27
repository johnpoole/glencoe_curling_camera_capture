#!/usr/bin/env python3
import os
import time
import pygame

IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "images",
    "hdmi.jpg",
)
CHECK_INTERVAL_SEC = 0.5


def main() -> None:
    # Do not force SDL_VIDEODRIVER; let SDL pick (KMSDRM on Pi OS Lite).
    os.putenv("SDL_NOMOUSE", "1")

    pygame.display.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)

    screen_rect = screen.get_rect()
    last_mtime = None

    while True:
        # Drain events to keep SDL happy.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        try:
            mtime = os.path.getmtime(IMAGE_PATH)
        except FileNotFoundError:
            time.sleep(CHECK_INTERVAL_SEC)
            continue

        if mtime != last_mtime:
            last_mtime = mtime
            try:
                img = pygame.image.load(IMAGE_PATH)
            except Exception:
                time.sleep(CHECK_INTERVAL_SEC)
                continue

            img_rect = img.get_rect()
            scale = min(
                screen_rect.width / img_rect.width,
                screen_rect.height / img_rect.height,
            )
            new_size = (
                int(img_rect.width * scale),
                int(img_rect.height * scale),
            )
            img = pygame.transform.smoothscale(img, new_size)
            img_rect = img.get_rect(center=screen_rect.center)

            screen.fill(0)
            screen.blit(img, img_rect)
            pygame.display.flip()

        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    main()
