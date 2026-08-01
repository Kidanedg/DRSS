FROM mcr.microsoft.com/devcontainers/base:ubuntu

ENV DEBIAN_FRONTEND=noninteractive

# Install system packages
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    zip \
    xz-utils \
    ca-certificates \
    openjdk-21-jdk \
    clang \
    cmake \
    ninja-build \
    pkg-config \
    libgtk-3-dev \
    libglu1-mesa \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Flutter SDK
ENV FLUTTER_HOME=/opt/flutter

RUN git clone \
    --depth 1 \
    --branch stable \
    https://github.com/flutter/flutter.git \
    ${FLUTTER_HOME}

ENV PATH="${FLUTTER_HOME}/bin:${FLUTTER_HOME}/bin/cache/dart-sdk/bin:${PATH}"

# Enable Flutter and preload artifacts
RUN flutter --version
RUN flutter config --enable-web
RUN flutter precache

# Install Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs

# Install Firebase CLI
RUN npm install -g firebase-tools

# Verify tools
RUN dart --version
RUN flutter --version
RUN node --version
RUN npm --version
RUN firebase --version

# Workspace
WORKDIR /workspaces

CMD ["/bin/bash"]
