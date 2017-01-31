Starting up...


1. Checkout the code locally somewhere.

2. setup virtualenv at that directory, pip install virtualenvwrapper

3. mkvirtualenv eventm

3. pip install -r requirements.txt  

4. sudo apt-get install node-less

To run locally,


0. workon eventm

1. from the application root dir, run gen-local.sh first time and then to update the config files when changed

2. from the application root dir, run launch-local.sh to start the local server

To deploy in dev or prod,

1. from the application root dir, run deploy.sh dev (for dev environment)

cofig: mkvirtualenv : http://stackoverflow.com/questions/12232421/virtualenvwrapper-commands-arent-working
