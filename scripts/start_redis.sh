#!/bin/bash
# Install and start Redis
if ! command -v redis-server &> /dev/null; then
    apt-get update && apt-get install -y redis-server
fi

# Start Redis server
redis-server --daemonize yes --bind 127.0.0.1 --port 6379
echo "Redis started on port 6379"
