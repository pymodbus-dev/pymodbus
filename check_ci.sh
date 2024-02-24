#!/bin/bash

set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT


codespell
ruff check --fix --exit-non-zero-on-fix .
pylint --recursive=y examples pymodbus test
mypy pymodbus
pytest --cov --numprocesses auto
echo "Ready to push"
