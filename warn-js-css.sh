#!/bin/bash
base_dir=`dirname $0`
cd $base_dir
./reduce-js.sh  www/templates/dashboard/twitter/dashboard.html /tmp/twitter_minified.js
./reduce-js.sh  www/templates/dashboard/instagram/ig-dashboard.html /tmp/ig_minified.js
./reduce-css.sh  www/templates/dashboard/instagram/ig-base-dashboard.html /tmp/ig_minified.css
./reduce-css.sh www/templates/dashboard/common/base_dashboard.html /tmp/base_dashboard.css
