#!/bin/sh
set -eu
cd /work
export PYTHONPATH=/work
exec python -m unittest discover -s /tests -p 'test_*.py' -v
