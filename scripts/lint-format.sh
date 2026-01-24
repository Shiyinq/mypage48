#!/bin/sh -e

# set -x
if [ -d ".venv" ]; then
    echo "Activating .venv..."
    source .venv/bin/activate
fi

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src --exclude=__init__.py,_example
isort src --profile black
black src