#!/bin/bash
# lingflow CLI Wrapper Script
# Used by lingflowAdapter in lingmessage

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Run the Python CLI
cd "$PROJECT_ROOT"
python -m lingflow.cli "$@"
