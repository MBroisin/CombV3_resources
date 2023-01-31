#!/bin/bash

set -x

file_stem=${1:?provide a file stem, e.g. 22-09-15T124500Z}
dur_s=${2:?duration in seconds}
month_dir=$3
day_dir=$4


#timeout_s=${3:-5}

function log_t() {
    nowt=$(/bin/date --utc "+%H:%M:%S.%2N")
    echo "[M] ${nowt} $1"
}


ERR="\033[41m"
BLU='\033[34m'
OKGREEN='\033[92m'
ENDC="\033[0m"
WARNING='\033[93m'

#timeout_s=5
timeout_s=$(( dur_s + 3 ))
#timeout_s=5

#here=$( dirname -- "$0" ; )
here="/home/sting/accel_measurements/accel-logger/bash_utils"
hostfile=$here/pssh/cam_helpers.hosts

if [ -f "$hostfile" ] ;
then
	echo "[All ok with $hostfile hosts lists"
else
	echo "[OH no hostfile list doesnt found $hostfile"
fi


ruser=pi

rscript=/home/pi/bin/do_vibe_vid.sh
#rscript=/home/pi/bin/echo_to_file.sh

# nohup seems to break things!
NOHUP=
#NOHUP=nohup

echo -e ${OKGREEN} "[I] first stage: record video (dur: ${dur_s} sec)" ${ENDC}
log_t "will start cam recording (bg). (timeout: ${timeout_s} s "


parallel-ssh --hosts=${hostfile} --user ${ruser} --inline -t ${timeout_s} \
    "${NOHUP} ${rscript} $file_stem $dur_s ${month_dir} ${day_dir} " &
vid_pid=$!

#log_t "spoof long running command after pssh launched."
#sleep 4

log_t "waiting for vid recording to complete (pid: $vid_pid)"
wait $vid_pid

sleep 2
log_t "now run in blocking mode: 2nd stage"
echo -e ${OKGREEN} "[I] second stage: convert video" ${ENDC}
for i in `seq 1 5` ; do echo -e ${OKGREEN} "=======" ${ENDC} ; done 

rscript2=/home/pi/bin/wrap_vid.sh
parallel-ssh --hosts=${hostfile} --user ${ruser} --inline -t ${timeout_s} \
    "${NOHUP} ${rscript2} $file_stem $dur_s ${month_dir} ${day_dir} " 
code2=$?

echo "[I] 2nd stage has code $code2."

set +x 

#log_t "now run in blocking mode: 3rd stage"
#echo -e ${OKGREEN} "[M] third stage: transfer files to archive " ${ENDC}

# for rhost in ... hostfile {if rhost !^#}
#rpi_base_src=/home/pi/acc2022/space
#rpi_dest=/home/pi/PC/hive1/acc2022/test_data/
#ssh pi@grazhut-hive1-rpi3.local "echo rsync -a --remove-sent-files ${rpi_base_src}/ $rpi_dest/ "
##rsync -a --remove-sent-files "../bash_utils/data/" "/home/sting/network/hive1/acc2022/test_data/"
##rsync -a --remove-sent-files 
