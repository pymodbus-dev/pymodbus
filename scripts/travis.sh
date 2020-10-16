#!/bin/bash -e
set -x
if [ "$TRAVIS_OS_NAME" = osx ]; then
  VIRTUAL_ENV="$HOME/.virtualenvs/python3.8"
  virtualenv "$VIRTUAL_ENV"
  source "$VIRTUAL_ENV/bin/activate"
fi

eval "$@"
