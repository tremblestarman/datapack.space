#!/bin/bash
while :
do
    parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
    cd "$parent_path"
    echo robot run at $(date +"%Y-%m-%d %T").
    xvfb-run /usr/local/bin/python3 -u "$parent_path"/update.py > "$parent_path"/robot.log 2>&1
    echo force-quit at $(date +"%Y-%m-%d %T").
    "$parent_path"/force-quit.sh
    echo build index at $(date +"%Y-%m-%d %T").
    cd util || exit
    ./indexer > indexer.log 2>&1
    cd "$parent_path"
    echo backup at $(date +"%Y-%m-%d %T").
    mysqldump -u root -p$MYSQLPASSWORD datapack_collection -P 3306 datapacks tags authors datapack_tags datapacks_related authors_related datapacks_log datapacks_ii_queue > "$parent_path"/datapack_collection.sql
    echo reset prccess at $(date +"%Y-%m-%d %T").
    ps aux | grep "/update.py" |  awk '{print $2}' | xargs kill -9
    sleep 10800
done
