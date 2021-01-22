#!/bin/bash

set -e

echo "Text for stderr" 1>&2

for number in {1..25}
do
echo "$number "
sleep 1
done

echo "More text for stderr" 1>&2