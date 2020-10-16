#!/bin/bash -e
set -x
if [ "$TRAVIS_OS_NAME" = osx ]; then
  virtualenv "$VIRTUAL_ENV"
  source "$VIRTUAL_ENV/bin/activate"
fi

eval "$@"
