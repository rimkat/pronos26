#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip pour supporter les paquets modernes
pip install --upgrade pip

# Installation en mode "no-cache" et "only-binary" pour éviter la compilation
pip install --no-cache-dir --only-binary=:all: -r requirements.txt