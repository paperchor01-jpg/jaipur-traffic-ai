# 1. Start with a clean Python Linux computer
FROM python:3.10-slim

# 2. Install SUMO, a fake monitor (Xvfb), and web-streaming tools (noVNC)
RUN apt-get update && apt-get install -y \
    sumo \
    sumo-tools \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

# 3. Create a folder for your app
WORKDIR /app

# 4. Copy all your files from GitHub into this cloud computer
COPY . .

# 5. Install PyTorch and your Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# 6. Make the startup script executable
RUN chmod +x start.sh

# 7. Open the port for the web browser
EXPOSE 8080

# 8. Turn on the engine
CMD ["./start.sh"]