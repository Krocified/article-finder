#!/bin/bash
cd "$(dirname "$0")"
python3 fetch-articles.py
echo ""
echo "Press Enter to close..."
read
