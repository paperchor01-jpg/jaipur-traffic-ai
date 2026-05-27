# 1. Start with a clean Python Linux computer
FROM python:3.10-slim

# 2. Install SUMO, fake monitor, web tools, AND 3D Graphics Libraries
RUN apt-get update && apt-get install -y \
    sumo \
    sumo-tools \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
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
