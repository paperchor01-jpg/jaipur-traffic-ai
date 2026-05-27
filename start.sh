#!/bin/bash

# 1. Start the virtual frame buffer (the fake monitor)
Xvfb :99 -screen 0 1024x768x16 &
export DISPLAY=:99

# 2. Start the window manager (draws the grey background)
fluxbox &

# 3. Start the VNC server (plugs in the video cable)
x11vnc -display :99 -nopw -listen localhost -xkb -ncache 10 -ncache_cr -forever &

# 4. Start the web streaming software IN THE BACKGROUND
websockify --web=/usr/share/novnc/ ${PORT} localhost:5900 &

# 5. Wait 5 seconds to let the monitor fully turn on
sleep 5

# 6. Run the AI engine IN THE FOREGROUND to trap the bug
python simulation.py
