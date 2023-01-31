#!/bin/bash

cd "/home/sting/accel_measurements/accel-logger/DataHandling/"

python_exec="../../acc_python_venv/accenv/bin/python"

# Folder structure  
month=$(date -u +"%m")
day=$(date -u +"%d")

fold="../bash_utils/data/$month/$day/"
mkdir -p $fold

# Shared file name
filestem=$(date -u +"%Y-%m-%dT%H%M%S%Z")
acc_id="acc_"

# Cam recording launch (bg)
echo "do pssh stuff here to launch cam recording with $filestem name for the file"

# Acc recording launch
#cd ../DataHandling/
#timeout_s=$(( $1 + 3 ))

#timeout $(( $1 + 5 )) "$python_exec" vibs_listen.py -d "$1" -f "$fold$acc_id$filestem"
"$python_exec" vibs_listen.py -d "$1" -f "$fold$acc_id$filestem"


# Store files in safe place
# source: including trailing / --> only take sub-directories 
# dest:   including trailing / --> write all results inside this directory
rsync -a --remove-sent-files "../bash_utils/data/" "/home/sting/network/hive1/acc2022/test_data/"

# regular ssh non0interactive rsync 
# for rpi in rpi_list
#   ssh rsync local --> archive

