#!/bin/bash

# Build the Tailwind CSS file using the standalone binary
# You must have 'tailwindcss' executable in the root directory

if [ ! -f "./tailwindcss" ]; then
    echo "❌ tailwindcss binary not found!"
    echo "   Please download it first:"
    echo "   curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64"
    echo "   chmod +x tailwindcss-linux-x64 && mv tailwindcss-linux-x64 tailwindcss"
    exit 1
fi

./tailwindcss -i ./blog/css/input.css -o ./blog/css/tailwind-output.css --minify
echo "✅ CSS built to blog/css/tailwind-output.css"
