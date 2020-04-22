#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path" || exit
touch robot.log
touch crontab.log
chmod 666 *.log
cd admin || exit
go build admin.go
go build language.go
go build schema_check.go
echo admin done at $(date +"%Y-%m-%d %T").
cd ../util || exit
go build indexer.go
touch indexer.log
chmod 666 indexer.log
echo indexer done at $(date +"%Y-%m-%d %T").
cd .. || exit
go build -o server main.go model.go router.go
echo server done at $(date +"%Y-%m-%d %T").
