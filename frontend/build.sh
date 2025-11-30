#!/bin/bash
# Build script to ensure old files are removed and new React app is built

echo "Cleaning old build files..."
rm -rf ../app/static/*

echo "Building React app..."
npm run build

echo "Build complete! Files in app/static/:"
ls -la ../app/static/

