DIR="`pwd`"/"`dirname $0`"
rm -f $DIR/console.log
xvfb-run python3 -u $DIR/update.py > $DIR/console.log 2>&1
cd $DIR/util || exit
./indexer
