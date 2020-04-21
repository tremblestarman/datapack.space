#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"
xvfb-run /usr/local/bin/python3 -u "$parent_path"/update.py > "$parent_path"/robot.log 2>&1
"$parent_path"/force-quit.sh
cd util || exit
./indexer > indexer.log 2>&1
mysqldump -u root -p$MYSQLPASSWORD datapack_collection -P 3306 datapacks tags authors datapack_tags datapacks_related authors_related datapacks_log datapacks_ii_queue > /TheEndOfDatapack/datapack_collection.sql
ps aux | grep "/update.py" |  awk '{print $2}' | xargs kill -9