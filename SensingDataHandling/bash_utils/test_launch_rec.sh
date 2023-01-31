#!/bin/bash
#set -x 

dur_s=${1:?duration in seconds}

cd "/home/sting/accel_measurements/accel-logger/DataHandling/"

#cwd=$(pwd)
cwd="../bash_utils"
camtool=${cwd}/launch_all_vidrec.sh 

t_start=$(date +%s.%3N)
python_exec="../../acc_python_venv/accenv/bin/python"

# Folder structure  
month=$(date -u +"%m")
day=$(date -u +"%d")

fold="../bash_utils/accdata/$month/$day/"
mkdir -p $fold

function conv_bytes_humanread() {
	# https://serverfault.com/a/859005
	f_size=$( echo "${1}" | awk '{ split( "B KB MB GB TB PB" , v ); s=1; while( $1>1024 ){ $1/=1024; s++ } printf "%.2f %s", $1, v[s] }')
	echo ${f_size}
}
# Shared file name
filestem=$(date -u +"%Y-%m-%dT%H%M%S%Z")
acc_id="acc_"
acc_logfile=$fold$acc_id$filestem
echo "[M] logfile for accel data is ${acc_logfile}"

# Cam recording launch (bg)
echo "do pssh stuff here to launch cam recording with $filestem name for the file"
echo " ---> stem:   $filestem duration: $dur_s s logdirs: month $month day $day "
echo " ---> to run: $camtool $filestem $dur_s $month $day &"

$camtool $filestem $dur_s $month $day  &

#sleep ${dur_s} &
vid_pid=$!
vid_code=$?


# Acc recording launch
#cd ../DataHandling/
timeout_s=$(( $1 + 10 ))

#timeout $(( $1 + 5 )) "$python_exec" vibs_listen.py -d "$1" -f "$fold$acc_id$filestem"
timeout $timeout_s "$python_exec" vibs_listen.py -d "$1" -f ${acc_logfile}
#sleep $timeout_s 
acc_pid=$!
acc_code=$?

echo "- waiting for vid to finish"
wait $vid_pid
echo "- waiting for acc rec to finish"
wait $acc_pid
echo "[I] exit code from vid: ${vid_code} | from acc: ${acc_code}"

# check size before tx
sleep 1
echo "[I] currend dir is : $(pwd)"
f_sz=$(stat -c '%s' ${acc_logfile} )
# https://serverfault.com/a/859005
f_size=$( echo "${f_sz}" | awk '{ split( "B KB MB GB TB PB" , v ); s=1; while( $1>1024 ){ $1/=1024; s++ } printf "%.2f %s", $1, v[s] }')

echo "[M]  accfile is ${f_size}"

sleep 1


# Store files in safe place
# source: including trailing / --> only take sub-directories 
# dest:   including trailing / --> write all results inside this directory
relative_dest=periodic_recordings_2022/
sting_base_dest=/home/sting/network/hive1/acc2022/
sting_dest=${sting_base_dest}/${relative_dest}
rpi_base_src=/home/pi/acc2022/space
rpi_base_dest=/home/pi/PC/hive1/acc2022/
rpi_dest=${rpi_base_dest}/${relative_dest}

tx_t0=$(date +%s.%3N)
rsync -a --remove-sent-files "../bash_utils/accdata" "$sting_dest"
#rsync -a --remove-sent-files "../bash_utils/data/" "/home/sting/network/hive1/acc2022/test_data/"
tx_t1=$(date +%s.%3N)
rhosts="pi@grazhut-hive1-rpi2.local pi@grazhut-hive1-rpi4.local"
#rhosts="pi@grazhut-hive1-rpi3.local"
for host in $rhosts; 
do
	ssh $host "echo -ne '\t'; hostname; echo -ne '\tpre : '; df -h . |sed 1d; rsync -a --remove-sent-files ${rpi_base_src}/ $rpi_dest/ ; echo -ne '\tpost: '; df -h . |sed 1d;"
	#ssh $host "h=$(hostname); pre_space=$(df -h . |sed 1d); echo \$h \$pre_space ; rsync -a --remove-sent-files ${rpi_base_src}/ $rpi_dest/ ; post_space=$(df -h . |sed 1d); echo $h $pre_space $post_space"
done
tx_t2=$(date +%s.%3N)

all_tx=$( echo "$tx_t2 - $tx_t0" | bc -l )

echo "[I] took ${all_tx} s to transfer data from all hosts."

# now check how many filese were generated.
count_tool="/home/sting/accel_measurements/accel-logger/bash_utils/expt_stats.sh"
nodes="h1p2 h1p4 accdata"
sz_log="/home/sting/accel_measurements/logs/expt_log.${month}-${day}.log"
echo "[I] will write mini info to $sz_log (for nodes '$nodes')"
t_end=$(date +%s.%3N)
LC_NUMERIC="en_US.UTF-8" # set this so printf doesn't complain about bc output
tot_expt_dur=$( echo "$t_end - $t_start" | bc -l )
printf 'Expt %s finished. (dur %d s) took %0.2f s\n' "$filestem" "$dur_s" "$tot_expt_dur" >> $sz_log
echo "[I] expt ${filestem} finished. (dur $dur_s) took $tot_expt_dur s"
sz_arr=()
for n in $nodes;
do
	sz_str=$( $count_tool $filestem $month $day $n )
	by=$( echo $sz_str | cut -d' ' -f8 | tr -d '(' )
	#echo -e "\t$sz_str, $by, "
	sz_arr+=("${by}")
	printf "\t$sz_str\n"
	printf "\t$sz_str\n" >> $sz_log
done

sz_tot=$(IFS=+; echo "$((${sz_arr[*]}))")
sz_tot_h=$(conv_bytes_humanread "$sz_tot" )

echo -e "\t[I] ${#sz_arr[@]} nodes -> totall $sz_tot_h ($sz_tot by)"
echo -e "\t[I] ${#sz_arr[@]} nodes -> totall $sz_tot_h ($sz_tot by)" >> $sz_log
# regular ssh non0interactive rsync 
# for rpi in rpi_list
#   ssh rsync local --> archive

