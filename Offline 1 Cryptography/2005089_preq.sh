#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Create virtual environment named 'venv'
python3 -m venv venv

# Activate the environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install necessary packages
pip install pycryptodome BitVector --break-system-packages


