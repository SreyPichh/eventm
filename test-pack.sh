#!/bin/bash
export TGTDIR=.
python $TGTDIR/pack-js.py  -i $TGTDIR/www/templates/dashboard/instagram/ig-dashboard.html   -o /tmp/ig-dashboard.html -m instagram_dashboard
diff -w $TGTDIR/www/templates/dashboard/instagram/ig-dashboard.html /tmp/ig-dashboard.html

python $TGTDIR/pack-js.py  -i $TGTDIR/www/templates/dashboard/common/base_dashboard.html   -o /tmp/base_dashboard.html -m common_dashboard
diff -w $TGTDIR/www/templates/dashboard/common/base_dashboard.html  /tmp/base_dashboard.html

