#!/bin/sh
set -eu
cp "${MINIEVAL_SOLUTION_DIR:-/solution}/totals.py" "${MINIEVAL_WORKDIR:-/work}/totals.py"
cp "${MINIEVAL_SOLUTION_DIR:-/solution}/cli.py" "${MINIEVAL_WORKDIR:-/work}/cli.py"
