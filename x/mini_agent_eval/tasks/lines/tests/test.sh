#!/bin/sh
set -eu
cd "${MINIEVAL_WORKDIR:-/work}"
export PYTHONPATH="${MINIEVAL_WORKDIR:-/work}"
exec "${MINIEVAL_PYTHON:-python}" -m unittest discover -s "${MINIEVAL_TESTS_DIR:-/tests}" -p 'test_*.py' -v
