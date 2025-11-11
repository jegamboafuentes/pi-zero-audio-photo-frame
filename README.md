# Pi zero audio photo frame: A Pirate Audio Player

This project turns a **Raspberry Pi Zero 2 W** and a **Pimoroni Pirate Audio Mini Speaker** into a dedicated, wall-mounted device for playing a single audio file.

It's designed to boot directly into the player, which displays a custom background image. The four buttons are mapped to custom controls for a personal, seamless experience.



## 🎵 Features

* **Custom Background:** Displays any photo (e.g., from a loved one) as the player background.
* **Full Playback Controls:**
    * **Button A:** Rewind 5 seconds (*Note: Requires .mp3 file*)
    * **Button B:** Fast-Forward 5 seconds (*Note: Requires .mp3 file*)
    * **Button X:** Play / Pause
    * **Button Y:** Play / Pause
* **Real-time Clock:** When playing, the screen shows a real-time `MM:SS` timestamp.
* **Polished UI:** Shows a "Loading..." message on startup and displays the custom image with rotated text.
* **Reliable Auto-start:** Uses a robust `systemd` user service to launch the player automatically after the audio system is ready.

---

## ⚙️ Hardware Required

* Raspberry Pi Zero 2 W
* Pimoroni Pirate Audio Mini Speaker
* MicroSD Card (8GB or larger)
* 5V Power Supply
* A Mac or PC with an SD card reader for initial setup

---

## 🚀 Installation Instructions

These instructions will guide you from a blank SD card to a fully working device.

### Part 1: Flash the SD Card

1.  Download and install the **Raspberry Pi Imager** for your Mac.
2.  Plug your SD card into your Mac.
3.  In Raspberry Pi Imager:
    * **Choose Device:** Raspberry Pi Zero 2 W
    * **Choose OS:** Raspberry Pi OS (other) -> **Raspberry Pi OS Lite (64-bit)**
    * **Choose Storage:** Select your microSD card.
4.  Click the **Gear icon** ⚙️ (Advanced Options) **before** writing:
    * Check **Enable SSH** -> "Use password authentication".
    * Check **Set username and password** (e.g., `admin` and a password you'll remember).
    * Check **Set Hostname** and enter `pirate-audio.local`.
    * Check **Configure wireless LAN** and enter the **2.4GHz** Wi-Fi SSID and password for your home.
    * Click **"Save"**.
5.  Click **"Write"** and wait for it to finish.

### Part 2: Critical Hardware Configuration

This is the most important step to make the audio work. The installer will eject the card; unplug it and plug it back into your Mac.

1.  Open the SD card in Finder (it should be named `bootfs`).
2.  Open the file `config.txt` with a plain text editor (like VS Code or Sublime Text).
3.  Scroll to the very bottom and **add** these lines to enable the Pirate Audio hardware:
    ```txt
    # --- Lines for Pirate Audio ---
    dtoverlay=hifiberry-dac
    gpio=25=op,dh
    dtparam=spi=on
    ```
4.  Now, we **must disable the Pi's built-in audio** to prevent conflicts. Find these two lines and edit them as shown:

    * **Find:** `dtparam=audio=on`
    * **Change to:** `#dtparam=audio=on` (Add a `#` to comment it out)

    * **Find:** `dtoverlay=vc4-kms-v3d`
    * **Change to:** `dtoverlay=vc4-kms-v3d,noaudio` (Add `,noaudio`)

5.  Save the `config.txt` file and eject the SD card.

### Part 3: First Boot and SSH

1.  Plug the SD card into your Pi and connect the power.
2.  Wait 1-2 minutes for it to boot and connect to your Wi-Fi.
3.  On your Mac's **Terminal**, type `ssh admin@pirate-audio.local` (or whatever username you set).
4.  If you get a "WARNING: REMOTE HOST" error, run this command to fix it:
    ```bash
    ssh-keygen -R pirate-audio.local
    ```
5.  Try connecting again. Enter your password to log in. You will see the `admin@pirate-audio:~ $` prompt.

---

## 💻 Project Setup

Now that you're logged into your Pi via SSH, let's install the software.

### Part 1: Install Dependencies

Run these commands one by one on your Pi to install all the necessary libraries:

```bash
sudo apt update
sudo apt install -y python3-pil python3-pygame python3-gpiozero python3-st7789 gpiod
```

### Part 2: Copy Your Project Files

On your **Mac's Terminal** (not the Pi one), use `scp` to send your files to the Pi.

1.  **Create the `Music` folder** on the Pi:
    
    Bash
    
    ```
    ssh admin@pirate-audio.local "mkdir -p /home/admin/Music"
    ```
    
2.  **Copy your files** (assuming they are in your Mac's `Downloads` folder):
    
    Bash
    
    ```
    # Copy your background image
    scp ~/Downloads/linaPic.png admin@pirate-audio.local:/home/admin/Music/
    
    # Copy your audio file (MP3 is STRONGLY recommended for seeking)
    scp ~/Downloads/audio.wav admin@pirate-audio.local:/home/admin/Music/
    
    # Copy the main Python script
    scp ~/Downloads/play_my_sound.py admin@pirate-audio.local:/home/admin/Music/
    ```
    

### Part 3: Test Manually

Before making it auto-start, let's test that the script works perfectly. In your **Pi's SSH terminal**:

Bash

```
python3 /home/admin/Music/play_my_sound.py
```

The screen should show "Loading...", then your picture. Press the buttons to test playback. (Press **Control+C** to exit).

---

## 🤖 A Brief About the Code

This script is built to be robust by forcing the hardware to work.

-   **`os.environ` Variables:** The first lines of the script are the most critical. They force `pygame` (the audio library) to use the `alsa` driver and connect *directly* to your hardware (`hw:0,0`), bypassing the Pi's buggy `pulsesink` software mixer. This is what makes the audio play reliably.
    
-   **`st7789` & `PIL`:** These libraries are used to control the display. We first show a "Loading..." text, then load your background image, resize it, and rotate it 90 degrees.
    
-   **`pygame.mixer`:** This library handles all audio. It loads the *entire* audio file into memory first (this is the "Loading..." part), which allows it to play instantly and (most importantly) get a real-time `MM:SS` timestamp.
    
-   **`gpiozero`:** This library handles all button presses. It also turns on the amplifier (GPIO 25) at the start and turns it off when the script exits.
    
-   **Threading:** The `show_message` and `update_time_display` functions use `threading.Timer` to run on a delay. This allows the script to show a message ("Paused") for 2 seconds and then make it disappear without freezing the whole program.
    

---

## 💡 How to Use

Once the script is running, the controls are simple:

-   **Button A:** Rewind 5 seconds. (*Note: This only works if you use an `.mp3` file, not `.wav`*).
    
-   **Button B:** Fast-Forward 5 seconds. (*Note: This only works if you use an `.mp3` file, not `.wav`*).
    
-   **Button X:** Play / Pause
    
-   **Button Y:** Play / Pause
    

---

## ⚡ Run Automatically on Boot

This is the final step to make your project a true appliance. We will use a `systemd` user service.

1.  In your **Pi's SSH terminal**, create the service file:
    
    Bash
    
    ```
    nano /home/admin/.config/systemd/user/pirate-player.service
    ```
    
2.  **Copy and paste** this entire configuration into the `nano` editor:
    
    Ini, TOML
    
    ```
    [Unit]
    Description=Pirate Audio Player
    # Waits for the audio system to be ready
    After=pulseaudio.service
    BindsTo=pulseaudio.service
    
    [Service]
    # Fixes for running in a "headless" environment
    Environment="GPIOZERO_PIN_FACTORY=lgpio"
    Environment="SDL_AUDIODRIVER=alsa"
    Environment="AUDIODEV=hw:0,0"
    
    # Gives the system 5 seconds to settle
    ExecStartPre=/bin/sleep 5 
    
    # Your script
    ExecStart=/usr/bin/python3 /home/admin/Music/play_my_sound.py
    WorkingDirectory=/home/admin/Music
    Restart=always
    
    [Install]
    WantedBy=default.target
    ```
    
3.  **Save and Exit:**
    
    -   Press **Control + O**
        
    -   Press **Enter**
        
    -   Press **Control + X**
        
4.  **Enable the Service:** Run these three commands one by one:
    
    Bash
    
    ```
    systemctl --user daemon-reload
    ```
    Bash
    
    ```
    systemctl --user enable pirate-player.service
    ```
    Bash
    
    ```
    sudo loginctl enable-linger admin
    ```
    
5.  **Reboot!**
    
    Bash
    
    ```
    sudo reboot
    ```
