#!/bin/bash
# demo_reset.sh — ARCANE Demo Environment Reset Script
# Cleans up all Docker containers and temp files, then restarts the warm sandbox.

echo "======================================"
echo "  ARCANE DEMO RESET"
echo "======================================"

# 1. Remove ALL arcane-* containers (running or stopped)
echo "[1/3] Removing arcane-* containers..."
CONTAINERS=$(docker ps -a --filter "name=arcane-" --format "{{.Names}}" 2>/dev/null)
if [ -n "$CONTAINERS" ]; then
    echo "$CONTAINERS" | xargs docker rm -f 2>/dev/null
    echo "      Removed: $CONTAINERS"
else
    echo "      No containers to remove."
fi

# 2. Clear all arcane regression test temp files
echo "[2/3] Clearing /tmp/arcane_regtest_*.py..."
REGTEST_FILES=$(ls /tmp/arcane_regtest_*.py 2>/dev/null)
if [ -n "$REGTEST_FILES" ]; then
    rm -f /tmp/arcane_regtest_*.py
    echo "      Cleared temp regression test files."
else
    echo "      No temp files to clear."
fi

# 3. Restart the warm sandbox container
echo "[3/3] Starting warm sandbox container..."
docker run -d --name arcane-warm arcane-sandbox sleep infinity > /dev/null 2>&1
# Pre-clone the demo repo into warm container
docker exec -i arcane-warm git clone https://github.com/aryanketkar-15/arcane-demo-repo . > /dev/null 2>&1
echo "      Warm container started and repo pre-cloned."

echo "======================================"
echo "DEMO RESET COMPLETE — sandbox warm, ready to go"
echo "======================================"
