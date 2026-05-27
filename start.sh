#!/bin/bash

# 1. Turn on the fake monitor (Resolution: 1280x720)
export DISPLAY=:99
Xvfb :99 -screen 0 1280x720x24 &
sleep 2

# 2. Start the window manager (so the SUMO window has borders/buttons)
fluxbox &

# 3. Turn on the screen-capturing software
x11vnc -display :99 -forever -nopw -bg -xkb

# 4. Run your JLN Marg SUMO simulation in the background
python simulation.py &

# 5. Start the web server to stream the video to your browser
websockify --web=/usr/share/novnc/ ${PORT} localhost:5900
