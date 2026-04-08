#!/bin/sh -e

# set -x
if [ -d ".venv" ]; then
    echo "Activating .venv..."
    source .venv/bin/activate
fi

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src scraper --exclude=__init__.py,_example
isort src scraper --profile black
black src scraper