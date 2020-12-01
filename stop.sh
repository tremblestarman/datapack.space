ps -ef|grep chromium-browser |grep -v grep|cut -c 9-15|xargs kill -9 >/dev/null 2>&1
ps -ef|grep Xvfb |grep -v grep|cut -c 9-15|xargs kill -9 >/dev/null 2>&1
ps aux | grep "/update.py" |  awk '{print $2}' | xargs kill -9
ps aux | grep "/robot.sh" |  awk '{print $2}' | xargs kill -9
