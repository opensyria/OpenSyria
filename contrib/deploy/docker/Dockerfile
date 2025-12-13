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

# Clone and build OpenSY
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

LABEL maintainer="OpenSY Developers <admin@opensy.net>"
LABEL description="OpenSY Node"
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

# Create opensy user
RUN useradd -m -s /bin/bash -u 1000 opensy

# Copy binaries from builder
COPY --from=builder /build/build/bin/opensyd /usr/local/bin/
COPY --from=builder /build/build/bin/opensy-cli /usr/local/bin/
COPY --from=builder /build/build/bin/opensy-tx /usr/local/bin/

# Create data directory
RUN mkdir -p /home/opensy/.opensy && \
    chown -R opensy:opensy /home/opensy/.opensy

# Default configuration
COPY contrib/deploy/docker/opensy.conf.default /home/opensy/.opensy/opensy.conf
RUN chown opensy:opensy /home/opensy/.opensy/opensy.conf

# Switch to opensy user
USER opensy
WORKDIR /home/opensy

# Data volume
VOLUME ["/home/opensy/.opensy"]

# P2P port
EXPOSE 9633

# RPC port (should only be exposed to trusted networks)
EXPOSE 9632

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD opensy-cli -datadir=/home/opensy/.opensy getblockchaininfo || exit 1

# Entry point
ENTRYPOINT ["opensyd"]
CMD ["-datadir=/home/opensy/.opensy", "-printtoconsole"]
