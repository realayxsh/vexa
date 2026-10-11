#!/bin/bash
# Yawr Support — Dependency installer
# Run ONCE on a fresh environment before start.sh

set -e

echo "[install] Installing all dependencies..."
python3 -m pip install -q -r requirements.txt

echo "[install] Done!"
python3 -c "import discord; print('[install] discord.py version:', discord.__version__)"
