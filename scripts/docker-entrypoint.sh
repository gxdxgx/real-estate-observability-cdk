#!/bin/bash
set -e

# Development container entrypoint
# Since we're running as root, no permission fixes needed

echo "Starting development container..."

# Install npm dependencies if node_modules is empty or doesn't exist
if [ ! -d /app/infrastructure/node_modules ] || [ -z "$(ls -A /app/infrastructure/node_modules)" ]; then
    echo "Installing npm dependencies..."
    cd /app/infrastructure
    npm install
fi

# Execute the original command
exec "$@"

