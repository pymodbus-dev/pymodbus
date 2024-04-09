# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    = -W --keep-going

# Put it first so that "make" without argument is like "make help".
help:
	sphinx-build -M help "." "_build" -W --keep-going

.PHONY: help Makefile

%: Makefile
	sphinx-build -M $@ "." "_build" -W --keep-going
