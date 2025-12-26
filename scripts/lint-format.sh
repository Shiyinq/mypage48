#!/bin/sh -e
set -x

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src --exclude=__init__.py,_example
isort src --profile black
black src