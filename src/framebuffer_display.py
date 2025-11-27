#!/usr/bin/env python3
import os
import time
import pygame

IMAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "hdmi.jpg")
CHECK_INTERVAL_SEC = 0.5

def main() -> None:
    # Use framebuffer console, not X
    os.putenv("SDL_NOMOUSE", "1")

    pygame.display.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)

    screen_rect = screen.get_rect()
    last_mtime = None

    while True:
        # Drain events to avoid SDL complaining
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

            # Overlay a changing timestamp so you can see that redraws are happening
            try:
                pygame.font.init()
                font = pygame.font.Font(None, 36)
                import datetime
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                text_surf = font.render(ts, True, (255, 255, 255))
                text_rect = text_surf.get_rect()
                text_rect.bottomright = (screen_rect.right - 10, screen_rect.bottom - 10)
                screen.blit(text_surf, text_rect)
            except Exception:
                pass

            pygame.display.flip()

        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
