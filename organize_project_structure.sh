#!/bin/bash

set -e

echo "[INFO] Creating professional project structure..."

mkdir -p "Smart Dual-Gate System"
mkdir -p "Development And Testing"
mkdir -p "Documentation And Archives"

echo "[INFO] Moving core project folders..."

git mv ai "Smart Dual-Gate System/" 2>/dev/null || mv ai "Smart Dual-Gate System/"
git mv auth "Smart Dual-Gate System/" 2>/dev/null || mv auth "Smart Dual-Gate System/"
git mv config "Smart Dual-Gate System/" 2>/dev/null || mv config "Smart Dual-Gate System/"
git mv core "Smart Dual-Gate System/" 2>/dev/null || mv core "Smart Dual-Gate System/"
git mv database "Smart Dual-Gate System/" 2>/dev/null || mv database "Smart Dual-Gate System/"
git mv hardware "Smart Dual-Gate System/" 2>/dev/null || mv hardware "Smart Dual-Gate System/"
git mv utils "Smart Dual-Gate System/" 2>/dev/null || mv utils "Smart Dual-Gate System/"
git mv web_dashboard "Smart Dual-Gate System/" 2>/dev/null || mv web_dashboard "Smart Dual-Gate System/"
git mv main.py "Smart Dual-Gate System/" 2>/dev/null || mv main.py "Smart Dual-Gate System/"

echo "[INFO] Moving optional/dev folders..."

[ -d yolo_dataset ] && git mv yolo_dataset "Development And Testing/" 2>/dev/null || true
[ -d archive_cleanup ] && git mv archive_cleanup "Documentation And Archives/" 2>/dev/null || true
[ -d logs ] && git mv logs "Development And Testing/" 2>/dev/null || true
[ -d cameras ] && git mv cameras "Development And Testing/" 2>/dev/null || true
[ -d services ] && git mv services "Development And Testing/" 2>/dev/null || true

echo "[INFO] Removing cache folders..."

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete

echo "[INFO] Done."
echo
echo "Run project now using:"
echo "cd 'Smart Dual-Gate System'"
echo "python3 main.py"
