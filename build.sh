#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path" || exit
touch robot.log
chmod 666 robot.log
cd admin || exit
go build admin.go
go build language.go
go build schema_check.go
cd ../util || exit
go build indexer.go
touch indexer.log
chmod 666 indexer.log
cd .. || exit
go build -o server main.go model.go router.go
