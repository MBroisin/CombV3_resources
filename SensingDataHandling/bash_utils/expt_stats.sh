#!/bin/bash

# count size and number of files from a given file stem
# args: 
# $file_stem $month_dir $day_dir $node [-v/--verb]

#set -x

function get_sz_by () {
	f_sz=$(stat -c '%s' "${1}" )
	echo $f_sz
}
function conv_bytes_humanread() {
	# https://serverfault.com/a/859005
	f_size=$( echo "${1}" | awk '{ split( "B KB MB GB TB PB" , v ); s=1; while( $1>1024 ){ $1/=1024; s++ } printf "%.2f %s", $1, v[s] }')
	echo ${f_size}
}

function get_sz_humanread () {
	f_sz=$( get_sz_by "$1" )
	f_size=$( conv_bytes_humanread "$f_sz" )
	echo $f_size
}


stem=${1?file stem}
month_dir=${2?month as %02d}
day_dir=${3?day as %02d}
node=${4?enter node (e.g. accdata, h1p2, etc)}

verb=$5

if [ -z "$verb" ] ; then
	verb=0
else
	if [ "$verb" == "-v" ] || [ "$verb" == "--verb" ]; then
		verb=1
	else
		verb=0
	fi
fi


#base=~/PC/hive1/acc2022/periodic_recordings_2022/${node}
#pth=${base}/$m/$d
relative_dest=periodic_recordings_2022/
sting_base_dest=/home/sting/network/hive1/acc2022/
sting_dest=${sting_base_dest}/${relative_dest}
rpi_base_src=/home/pi/acc2022/space
rpi_base_dest=/home/pi/PC/hive1/acc2022/
rpi_dest=${rpi_base_dest}/${relative_dest}
# convoluted but the above just got copied
base=${sting_dest}

pth=${base}/${node}/${month_dir}/${day_dir}/

#file_list=$(find $pth -name "*$stem*" -print0 )
#file_list=" ..."

readarray -d '' file_array < <(find $pth -name "*$stem*" -print0)

# https://stackoverflow.com/a/54561526
# readarray -d '' array < <(find . -name "$input" -print0)
#echo "[I] found ${#file_array[@]} files"

n=${#file_array[@]}
[ "$verb" -eq "1" ] && echo "[I] $n files matching stem ${stem} in pth ${pth}:"
#echo "   ${file_array}"

sz_arr=()
for f in "${file_array[@]}"
do
	# quote args incase of spaces in paths
	szh=$(get_sz_humanread "$f")
	szb=$(get_sz_by "$f")
	sz_arr+=("$szb")
	[ "$verb" -eq "1" ] && printf "%40s\t%10s\n" "$(basename $f)" "$szh"
	#echo "$(basename $f), $sz"
done
sz_tot=$(IFS=+; echo "$((${sz_arr[*]}))")
sz_tot_h=$(conv_bytes_humanread "$sz_tot" )

echo "[I] $node: $n files totalling $sz_tot_h ($sz_tot by)"


