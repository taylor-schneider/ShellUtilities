#!/bin/bash

set -e
set -x

python3 -m pip install wheel twine
python3 setup.py sdist bdist_wheel
