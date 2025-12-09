# OpenSyria GPU Miner for Vast.ai
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    libboost-all-dev \
    libevent-dev \
    libssl-dev \
    libsqlite3-dev \
    pkg-config \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create opensyria user
RUN useradd -m -s /bin/bash opensyria

# Set working directory
WORKDIR /home/opensyria

# Download and extract OpenSyria binaries (will be built from source)
# For now, we'll clone and build
RUN git clone https://github.com/opensyria/OpenSyria.git /home/opensyria/OpenSyria

WORKDIR /home/opensyria/OpenSyria

# Build OpenSyria
RUN cmake -B build -DBUILD_DAEMON=ON -DBUILD_CLI=ON -DBUILD_TESTS=OFF -DBUILD_GUI=OFF \
    && cmake --build build -j$(nproc)

# Create data directory
RUN mkdir -p /home/opensyria/.opensyria

# Copy startup script
COPY start-mining.sh /home/opensyria/start-mining.sh
RUN chmod +x /home/opensyria/start-mining.sh

# Set ownership
RUN chown -R opensyria:opensyria /home/opensyria

USER opensyria
WORKDIR /home/opensyria

# Expose P2P port
EXPOSE 9633

# Default command
CMD ["/home/opensyria/start-mining.sh"]
