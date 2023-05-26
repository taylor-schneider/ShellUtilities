#!/bin/bash

set -e
set -x

python3 -m pip install wheel twine
twine upload dist/* 
