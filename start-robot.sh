parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"
nohup ./robot.sh >> schedule.log 2>&1 &
