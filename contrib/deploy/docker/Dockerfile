FROM ubuntu:22.04 AS builder

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILD_TYPE=Release

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libevent-dev \
    libboost-dev \
    libboost-system-dev \
    libboost-filesystem-dev \
    libboost-test-dev \
    libsqlite3-dev \
    libzmq3-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and build OpenSyria
WORKDIR /build
COPY . /build/

RUN cmake -B build \
    -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
    -DBUILD_GUI=OFF \
    -DBUILD_TESTS=OFF \
    && cmake --build build -j$(nproc)

# =============================================================================
# Production image
# =============================================================================
FROM ubuntu:22.04

LABEL maintainer="OpenSyria Developers <admin@opensyria.net>"
LABEL description="OpenSyria Core Node"
LABEL version="1.0"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libevent-2.1-7 \
    libevent-pthreads-2.1-7 \
    libboost-system1.74.0 \
    libboost-filesystem1.74.0 \
    libsqlite3-0 \
    libzmq5 \
    libssl3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create opensyria user
RUN useradd -m -s /bin/bash -u 1000 opensyria

# Copy binaries from builder
COPY --from=builder /build/build/bin/opensyriad /usr/local/bin/
COPY --from=builder /build/build/bin/opensyria-cli /usr/local/bin/
COPY --from=builder /build/build/bin/opensyria-tx /usr/local/bin/

# Create data directory
RUN mkdir -p /home/opensyria/.opensyria && \
    chown -R opensyria:opensyria /home/opensyria/.opensyria

# Default configuration
COPY contrib/deploy/docker/opensyria.conf.default /home/opensyria/.opensyria/opensyria.conf
RUN chown opensyria:opensyria /home/opensyria/.opensyria/opensyria.conf

# Switch to opensyria user
USER opensyria
WORKDIR /home/opensyria

# Data volume
VOLUME ["/home/opensyria/.opensyria"]

# P2P port
EXPOSE 9633

# RPC port (should only be exposed to trusted networks)
EXPOSE 9632

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD opensyria-cli -datadir=/home/opensyria/.opensyria getblockchaininfo || exit 1

# Entry point
ENTRYPOINT ["opensyriad"]
CMD ["-datadir=/home/opensyria/.opensyria", "-printtoconsole"]
