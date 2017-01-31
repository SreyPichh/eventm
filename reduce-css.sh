#!/bin/bash
SCRIPT=`realpath $0`
export SCRIPTPATH=`dirname $SCRIPT`
export out=''
export wc=`cat $1 | grep  link | grep "/css/app/" | wc -l`
if [[ $wc -eq 0 ]]; then
	echo "No css found. Exiting hence"
else
	export list=`cat $1 | grep  link | grep "/css/app/" | awk -F'='  '{print $2;}'  | awk -F'"'  '{print $2;}'  | awk -F'>'  '{ print "www"$1; }'`
	for i in ${list[@]};
	do
	    out="$out $i"
	done
	date
	echo $out
	export now=`date +"%Y%m%d_%H%M%S"`
	cat $out > /tmp/input-$now.css
	gradle runYui -Pmyargs="--type css -o $2 /tmp/input-$now.css"
fi
echo "End of pack-css"
date
