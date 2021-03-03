#!/bin/bash
while :
do
  parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
  cd "$parent_path"

  # run spider
  echo spider run at $(date +"%Y-%m-%d %T").
  xvfb-run python3 -u "$parent_path"/__spider__.py >"$parent_path"/spider.log 2>&1

  # quit & kill all related process
  echo quit at $(date +"%Y-%m-%d %T").
  ps -ef|grep chromium-browser |grep -v grep|cut -c 9-15|xargs kill -15 >/dev/null 2>&1
  ps -ef|grep Xvfb |grep -v grep|cut -c 9-15|xargs kill -15 >/dev/null 2>&1
  ps -aux|grep "/__spider__.py"|awk '{print $2}'|xargs kill -15 >/dev/null 2>&1

  # sleep
  echo sleep at $(date +"%Y-%m-%d %T").
  sleep 7200
  echo --------
done
