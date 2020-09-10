#!/bin/bash -e

if [ "$TRAVIS_OS_NAME" = osx ]; then
  VIRTUAL_ENV="$HOME/.virtualenvs/pymodbus"
  python3 -m venv $VIRTUAL_ENV
#  if [ ! -x "$VIRTUAL_ENV/bin/python" ]; then
#    virtualenv "$VIRTUAL_ENV"
#  fi
  source "$VIRTUAL_ENV/bin/activate"
fi

eval "$@"
