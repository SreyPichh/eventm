#!/bin/bash
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/wtforms www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/linkedin www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/requests www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/requests_oauthlib www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/babel www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/pytz www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/httplib2 www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/httpagentparser www/ -s
ln $HOME/.virtualenvs/eventm/lib/python2.7/site-packages/crypto www/ -s

files=`find . -name "*.template"`
for file in $files;
do
	python www/gen_config.py local $file
done
