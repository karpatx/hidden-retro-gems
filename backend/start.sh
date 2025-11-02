#!/bin/bash
echo "Starting Hidden Gem Backend..."
cd "$(dirname "$0")"
uv run python main.py

