#!/bin/bash

set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT


codespell
ruff check --fix --exit-non-zero-on-fix .
pylint --recursive=y examples pymodbus test
zuban check pymodbus examples test
if [ $1 ]; then
 exit 1
fi
pytest -x --cov --numprocesses auto
echo "Ready to push"
