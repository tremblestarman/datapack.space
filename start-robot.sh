parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"
nohup ./robot.sh > crontab.log 2>&1 &
