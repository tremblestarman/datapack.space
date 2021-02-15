#!/bin/bash
while :
do
  parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
  cd "$parent_path"

  # run spider
  echo porter run at $(date +"%Y-%m-%d %T").
  /usr/local/bin/python3 -u "$parent_path"/__porter__.py >"$parent_path"/porter.log 2>&1

  # quit & kill all related process
  echo quit at $(date +"%Y-%m-%d %T").
  ps -aux|grep "/__porter__.py"|awk '{print $2}'|xargs kill -15 >/dev/null 2>&1

  # build index
  echo build index at $(date +"%Y-%m-%d %T").
  cd util || exit
  ./indexer > indexer.log 2>&1

  # backup database
  cd "$parent_path"
  MYSQLPASSWORD=#PASSWORD
  mysqldump -uroot -p$MYSQLPASSWORD datapack_collection -P 3306 >"$parent_path"/datapack_collection.sql

  # restart
  echo restart prccess at $(date +"%Y-%m-%d %T").
  echo --------
done