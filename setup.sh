#!/bin/bash

# Update package lists and install ffmpeg
apt install -y ffmpeg

# Install Python packages from requirements.txt
pip install -r requirements.txt
