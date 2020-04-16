#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"
xvfb-run /usr/local/bin/python3 -u "$parent_path"/update.py > "$parent_path"/robot.log 2>&1
cd util || exit
./indexer > indexer.log 2>&1
