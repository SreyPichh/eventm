#!/bin/bash

# Activate virtual environment.
workon eventm 

# Run GAE dev server.
export DSDIR=$HOME/.ds_eventm
if [ $# -eq 1 ]; then
	if [ "$1" = "-clean" ]; then
		rm -fr $DSDIR
	fi
fi

files=`find . -name "*.less"`
for file in $files;
do
	dirname=`dirname $file`
	filename=$(basename "$file")
	filename="${filename%.*}"
	out=$dirname/$filename.css
	lessc $file >  $out
	echo "Wrote $out from $file"
done

FULLPATH=`realpath $0`
THISDIR=`dirname $FULLPATH`
echo $THISDIR
# cd ..
cd google_appengine/
./dev_appserver.py --enable_sendmail --storage_path $DSDIR --log_level debug --admin_port 7000 $THISDIR/www/app.yaml
