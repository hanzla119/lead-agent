#!/bin/bash
echo "========================================================"
echo "🌐 Free 24/7 Mobile Tunnel Setup (Cloudflare Quick Tunnel)"
echo "========================================================"
echo "Starting your secure HTTPS link for mobile & laptop access..."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Download cloudflared if not present
if [ ! -f "cloudflared" ]; then
    echo "Downloading cloudflared binary..."
    curl -L --output cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
    chmod +x cloudflared
fi

echo "Connecting tunnel to http://localhost:8000..."
./cloudflared tunnel --url http://localhost:8000
