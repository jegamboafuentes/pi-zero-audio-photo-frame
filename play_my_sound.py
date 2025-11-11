#!/usr/bin/env python3

import os
import signal

# === ROTATION OPTION ===
ROTATE_90 = True
# =======================

# --- ALSA FIX FOR ESP32 AUDIO ---
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['AUDIODEV'] = 'hw:0,0'
# --------------------------------

import subprocess
import time
import threading
from gpiozero import OutputDevice, Button
from signal import pause
from PIL import Image, ImageDraw, ImageFont
import st7789
import pygame

# --- GPIO Buttons ---
AMP_PIN = 25
PIN_A = 5           # Back 7s
PIN_B = 6           # Cycle background
PIN_X = 16          # Play/Pause
PIN_Y = 24          # Play/Pause

# --- IMAGE FILES ---
IMAGE_LIST = [
    "/home/admin/Music/linaPic.png",   # original first ✅
    "/home/admin/Music/linaPic2.png",
    "/home/admin/Music/linaPic3.png",
    "/home/admin/Music/linaPic4.png",
]

AUDIO_FILE = "/home/admin/Music/audio.wav"
TEXT_COLOR = (255, 255, 255)

# --- Display ---
DC_PIN = 9
BL_PIN = 13

# --- Globals ---
display_timer = None
playback_timer = None
current_bg_index = 0   # Start with original image ✅

is_paused = False
base_image = None
img = None
draw = None
disp = None
FONT = None
FONT_SMALL = None

ST7789_ROTATION = 180 if ROTATE_90 else 0
SKIP_SECONDS = 7


# ---------------------------------------------------------
#                    DISPLAY HELPERS
# ---------------------------------------------------------

def load_background(path):
    """Loads and draws a background image."""
    global base_image, img, draw
    try:
        bg = Image.open(path).convert("RGB").resize((240, 240))
        base_image = bg
        img = base_image.copy()
        draw = ImageDraw.Draw(img)
        disp.display(img)
        print(f"Background changed to {path}")
    except Exception as e:
        print(f"Error loading {path}: {e}")
        show_message("Image missing", duration=1.2, size="large")


def clear_screen():
    global img
    if display_timer: display_timer.cancel()
    if playback_timer: playback_timer.cancel()
    img.paste(base_image)
    disp.display(img)


def show_message(message, duration=1.3, size="large"):
    global display_timer
    font = FONT if size == "large" else FONT_SMALL

    if display_timer: display_timer.cancel()
    if playback_timer: playback_timer.cancel()

    img.paste(base_image)
    bbox = draw.textbbox((0,0), message, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((240-tw)//2, (240-th)//2), message, font=font, fill=TEXT_COLOR)
    disp.display(img)

    display_timer = threading.Timer(duration, clear_screen)
    display_timer.start()


def update_time_display():
    global playback_timer

    if not pygame.mixer.music.get_busy() and not is_paused:
        clear_screen()
        return

    pos_ms = pygame.mixer.music.get_pos()
    if pos_ms < 0:
        pos_ms = 0

    sec = pos_ms // 1000
    mins = sec // 60
    secs = sec % 60

    time_str = f"{mins:02d}:{secs:02d}"

    img.paste(base_image)
    bbox = draw.textbbox((0, 0), time_str, font=FONT_SMALL)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((240-tw)//2, (240-th)//2), time_str, font=FONT_SMALL, fill=TEXT_COLOR)
    disp.display(img)

    playback_timer = threading.Timer(0.5, update_time_display)
    playback_timer.start()


# ---------------------------------------------------------
#                    AUDIO FUNCTIONS
# ---------------------------------------------------------

def play_pause():
    global is_paused, playback_timer

    if display_timer: display_timer.cancel()

    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        is_paused = True
        if playback_timer: playback_timer.cancel()
        clear_screen()
    else:
        if is_paused:
            pygame.mixer.music.unpause()
            is_paused = False
            update_time_display()
        else:
            pygame.mixer.music.play()
            is_paused = False
            update_time_display()


def skip_backward():
    """Button A: back 7 seconds."""
    global is_paused

    pos = pygame.mixer.music.get_pos()
    if pos < 0: pos = 0

    new_pos = max(0, pos - SKIP_SECONDS*1000)
    pygame.mixer.music.play(start=new_pos/1000)
    is_paused = False

    show_message(f"-{SKIP_SECONDS}s")
    update_time_display()


def cycle_background():
    """Button B: cycle all images including original."""
    global current_bg_index
    current_bg_index = (current_bg_index + 1) % len(IMAGE_LIST)
    load_background(IMAGE_LIST[current_bg_index])


# ---------------------------------------------------------
#                        MAIN
# ---------------------------------------------------------

try:
    # Display
    disp = st7789.ST7789(
        port=0, cs=1, dc=DC_PIN,
        backlight=BL_PIN,
        rotation=ST7789_ROTATION,
        spi_speed_hz=80_000_000
    )
    disp.set_backlight(True)

    img = Image.new("RGB", (240,240), (0,0,0))
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        FONT = ImageFont.load_default()
        FONT_SMALL = ImageFont.load_default()

    # Loading screen
    draw.text((80,110),"Loading...", font=FONT, fill=TEXT_COLOR)
    disp.display(img)

    # Amp
    amp = OutputDevice(AMP_PIN)
    amp.on()

    # Audio
    pygame.mixer.init()
    pygame.mixer.music.load(AUDIO_FILE)

    # Load first image (original)
    load_background(IMAGE_LIST[0])

    print("READY ✅")
    print("A = Back 7s")
    print("B = Change picture (cycles including original)")
    print("X/Y = Play/Pause")

    # Buttons
    button_A = Button(PIN_A)
    button_B = Button(PIN_B)
    button_X = Button(PIN_X)
    button_Y = Button(PIN_Y)

    button_A.when_pressed = skip_backward
    button_B.when_pressed = cycle_background
    button_X.when_pressed = play_pause
    button_Y.when_pressed = play_pause

    pause()

except KeyboardInterrupt:
    pygame.mixer.music.stop()
    disp.set_backlight(False)
    amp.off()

except Exception as e:
    print("Error:", e)
    try: pygame.mixer.music.stop()
    except: pass
    try: disp.set_backlight(False)
    except: pass
    try: amp.off()
    except: pass