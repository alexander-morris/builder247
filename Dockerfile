FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create .ssh directory and set permissions
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Setup SSH config to avoid host verification issues
RUN echo "StrictHostKeyChecking no" >> /root/.ssh/config

# Setup SSH server
RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/src /app/tests /app/docs /app/logs /app/workspace

# Copy source code
COPY . .

# Set permissions
RUN chmod -R 755 /app

# Expose SSH port
EXPOSE 22

# Create startup script
RUN echo '#!/bin/bash\n\
\n\
# Function to cleanup\n\
cleanup() {\n\
    echo "Shutting down services..."\n\
    pkill -f "python -u src/main.py"\n\
    /etc/init.d/ssh stop\n\
    exit 0\n\
}\n\
\n\
# Trap SIGTERM and SIGINT\n\
trap cleanup SIGTERM SIGINT\n\
\n\
echo "Starting SSH server..."\n\
/usr/sbin/sshd\n\
\n\
echo "Starting agent..."\n\
python -u src/main.py 2>&1 | tee /app/logs/agent.log &\n\
\n\
# Keep container running\n\
while true; do\n\
    sleep 1\n\
done\n\
' > /app/start.sh && chmod +x /app/start.sh

# Entry point script
ENTRYPOINT ["/app/start.sh"] 