DIR="`pwd`"/"`dirname $0`"
cd $DIR/admin || exit
go build admin.go
go build language.go
go build schema_check.go
cd ../util || exit
go build indexer.go
cd .. || exit
go build -o server main.go model.go router.go
