#!/bin/bash

set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT


codespell
pre-commit run --all-files
pylint --recursive=y examples pymodbus test
mypy pymodbus
pytest --numprocesses auto
echo "Ready to push"
