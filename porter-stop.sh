ps -aux|grep "/__porter___.py"|awk '{print $2}'|xargs kill -9 >/dev/null 2>&1
ps -aux|grep "/porter-run.sh"|awk '{print $2}'|xargs kill -9 >/dev/null 2>&1