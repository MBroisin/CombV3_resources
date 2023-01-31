#!/bin/bash

if [ "$1" == "-h" ]; then
  echo "Usage: `basename $0` [duration (in seconds)]"
  exit 0
fi

cd "/home/pi/Documents/CombV3_resources/SensingDataHandling/DataHandling/"

python_exec="python"

# Folder structure  
month=$(date -u +"%m")
day=$(date -u +"%d")

fold="../data/$month/$day/"
mkdir -p $fold

# Shared file name
filestem=$(date -u +"%Y-%m-%dT%H%M%S%Z")
acc_id="acc_"
acc_ext=".txt"

#timeout $(( $1 + 5 )) "$python_exec" vibs_listen.py -d "$1" -f "$fold$acc_id$filestem"
timeout $(( $1 + 10 )) "$python_exec" vibs_listen.py -d "$1" -f "$fold$acc_id$filestem$acc_ext"

