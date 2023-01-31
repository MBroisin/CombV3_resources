#!/bin/bash

# how long the loop should take
step="180 second"
#step="10 minute"

dur_s=90

# seq just makes a counter
for i in `seq 1 10000` ; do
	now=$( date +"%s.%3N" )
	t_next=$( date --date "now + $step" +"%s.%3N" )
	echo "[iteration $i] start ${now}"
	# stop a small time, spoof computation
	sleep 1.3
	/home/sting/accel_measurements/accel-logger/bash_utils/test_launch_rec.sh $dur_s
	# compute idle time remaining
	now2=$( date +"%s.%3N" )
	elap=$( echo "${now2} - ${now}" | bc -l )
	dt=$( echo " ${t_next} - ${now2}" | bc -l )
	#printf "iteration %3d | took %.2f s. Sleep %.2fs until %s" $i $elap $dt $next
	echo "iteration $i | took ${elap} s. Sleep $dt until $t_next" $i $elap $dt $next
	sleep $dt

done

