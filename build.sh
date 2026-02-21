#!/bin/bash
set -e

pip install pyinstaller

pyinstaller --onefile --name SwitchCost main.py

echo "Built binary at dist/SwitchCost"
