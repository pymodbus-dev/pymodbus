#!/bin/bash

set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT


codespell
black --safe --quiet examples/ pymodbus/ test/
isort .
pylint --recursive=y examples pymodbus test
flake8
pytest --numprocesses auto
echo "Ready to push"
