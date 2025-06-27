#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install dependencies required for building Python
sudo apt install -y wget build-essential libreadline-dev libncursesw5-dev \
libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev \
libffi-dev zlib1g-dev

# Download Python 3.13.1 source code
wget https://www.python.org/ftp/python/3.13.2/Python-3.13.2.tar.xz

# Extract the archive
tar -xf Python-3.13.2.tar.xz

# Navigate to the extracted directory
cd Python-3.13.2

# Configure the build with optimizations
./configure --enable-optimizations

# Build and install Python (this will take some time)
# Using altinstall to avoid replacing the default python binary
sudo make altinstall

# Verify the installation
python3.13 --version

echo "Python 3.13.1 has been installed successfully!"
echo "You can run it using the 'python3.13.2' command."
