#!/bin/bash
set -e

export PYTHONPATH=$PWD
export PATH=$PWD/.venv/bin:$PATH

pyinstaller --onefile --name SwitchCost main.py

echo "Built binary at dist/SwitchCost"
