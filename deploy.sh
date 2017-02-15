#!/bin/bash
if [ $# -ne 1 ]; then
	echo "Syntax: $0 [dev|prod] "
	exit 1
fi


export TGTDIR=$HOME/.eventm

#rm -fr $TGTDIR
if [ -d "$TGTDIR" ]; then
	cd $TGTDIR
	echo "$TGTDIR already exists. Pulling latest source from git ... "
	git checkout master
	git pull
else
	git clone https://github.com/SreyPichh/eventm.git $TGTDIR
fi

files=`find $TGTDIR/www -name "*.template"`
for file in $files;
do
	python $TGTDIR/www/gen_config.py $1 $file
done
files=`find $TGTDIR/www -name "*.less"`
for file in $files;
do
	dirname=`dirname $file`
	filename=$(basename "$file")
	filename="${filename%.*}"
	out=$dirname/$filename.css
	lessc $file >  $out
	echo "Wrote $out from $file"
done

rm -fr $TGTDIR/buildwww
cp -r $TGTDIR/www $TGTDIR/buildwww

find $TGTDIR/buildwww -name \*.less | xargs rm
echo "Deleting .less files"

# Instagram Pack
#python $TGTDIR/pack-js.py  -i $TGTDIR/www/templates/dashboard/instagram/ig-dashboard.html   -o $TGTDIR/buildwww/templates/dashboard/instagram/ig-dashboard.html -m instagram_dashboard
#diff -w  $TGTDIR/www/templates/dashboard/instagram/ig-dashboard.html   $TGTDIR/buildwww/templates/dashboard/instagram/ig-dashboard.html
echo "**************** End of Diff *****************"

#Manually creating soft links for external libraries that appengine doesnt understand
cp -r $HOME/.virtualenvs/eventm/local/lib/python2.7/site-packages/wtforms $TGTDIR/buildwww/wtforms
cp -r $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/linkedin $TGTDIR/buildwww/linkedin
cp -r $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/requests $TGTDIR/buildwww/requests
cp -r $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/requests_oauthlib $TGTDIR/buildwww/requests_oauthlib
cp -r $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/babel $TGTDIR/buildwww/babel
cp -r $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/pytz $TGTDIR/buildwww/pytz
cp -r $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/httplib2 $TGTDIR/buildwww/httplib2
cp -r $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/httpagentparser $TGTDIR/buildwww/httpagentparser
cd $HOME/.eventm/google_appengine/
#./appcfg.py -A sport-cambodia -V uno update $TGTDIR/buildwww/ --no_cookies date
./appcfg.py -A sport-cambodia -V uno update $TGTDIR/buildwww/ --no_cookies date
# cd ..

# appc update $TGTDIR/buildwww/app.yaml
# appcfg.py update_dispatch $TGTDIR/buildwww
# appcfg.py update_indexes $TGTDIR/buildwww
# datefg.py
