#!/bin/bash
SCRIPT=`realpath $0`
export SCRIPTPATH=`dirname $SCRIPT`
export out=''
export list=`cat $1 | grep  script | grep "/js/app/" | awk -F'='  '{print $2;}'  | awk -F'"'  '{print $2;}'  | awk -F'>'  '{ print "www"$1; }'`
for i in ${list[@]};
do
    out="$out $i"
done
date
echo $out
gradle runTool -Pmyargs="--compilation_level WHITESPACE_ONLY $out --js_output_file $2"
#gradle runYui -Pmyargs="--nomunge $out -o $2"
date
