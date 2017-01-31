#!/usr/bin/python
import sys
import json
from jinja2 import Template
import os
import yaml

def process_templatefile(env, infile):
    current_dir = os.path.dirname( os.path.abspath(__file__) )
    yamlfile = os.path.join(current_dir, '../env.yaml')
    mydict = dict()
    with open(yamlfile) as f1:
        data = f1.read()
        mydict = yaml.load(data)#json.loads(data)
    if not env in mydict:
        print 'Enviroment: %s not present in yaml. Quitting hence'
        sys.exit(2)
    else:
        with open(infile) as f:
            data = f.read()
            template = Template(data)
            rendered = template.render(mydict[env])
            output_dir = os.path.dirname( os.path.abspath(infile) )
            output_file = os.path.splitext(os.path.basename(infile))[0]
            final_file = os.path.join(output_dir, output_file)
            with open(final_file, 'w') as f3:
                f3.write(rendered)
                print 'Wrote %s from %s [env: %s ] ' % (final_file, infile, env)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Syntax: %s <env name> <template filename> " % sys.argv[0]
        sys.exit(1)
    else:
        process_templatefile(sys.argv[1], sys.argv[2])
