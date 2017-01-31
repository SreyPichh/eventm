import sys
from mako.template import Template
from datetime import datetime
import os
import sys
import getopt
import subprocess

def pack_resource(filename, outfilename, packname, file_type='js'):
    mydict = dict()
    now = datetime.utcnow()
    pack_key =  'packed_%s_%s' % (file_type, packname)
    mydict[pack_key] = '/assets/js/packed_%s-%s.js' % (packname, now.strftime('%Y%m%d%H%M%S')) if file_type == 'js' \
                                else '/assets/css/packed_%s-%s.css' % (packname, now.strftime('%Y%m%d%H%M%S'))
    dirName =  os.path.dirname(os.path.realpath(__file__))
    jsoutputfile = 'buildwww/%s' % mydict[pack_key]
    fq_jsoutputfile = os.path.join(dirName, jsoutputfile)
    inputFile = os.path.join(dirName, filename)
    subprocess.call([ os.path.join(dirName, 'reduce-%s.sh' % file_type),  inputFile, fq_jsoutputfile])
    return mydict


def pack_resources(filename, outfilename, packname):
    mydict = dict()
    js_dict  = pack_resource(filename, outfilename, packname, 'js')
    css_dict = pack_resource(filename, outfilename, packname, 'css') 
    mydict['original'] = False
    mydict.update(js_dict)
    mydict.update(css_dict)
    print mydict
    dirName =  os.path.dirname(os.path.realpath(__file__))


    inputFile = os.path.join(dirName, filename)
    with file(inputFile) as f:
        contents = f.read()
    template = Template(contents)
    out = template.render(**mydict)
    fq_outputfile = os.path.join(dirName, outfilename)
    with open(fq_outputfile, 'w') as the_file:
        the_file.write(out.encode('ascii', 'replace'))


def process_args(argv):
    optlist, args = getopt.getopt(argv, 'i:o:m:',['input', 'output', 'macro'])
    input_file = None
    output_file = None
    macro_name = None
    for opt, arg in optlist:
        if opt in ('-i', '--input'):
            input_file = arg
        elif opt in ('-o', '--output'):
            output_file = arg
        elif opt in ('-m', '--macro'):
            macro_name = arg
    pack_resources(input_file, output_file,  macro_name)


if __name__ == "__main__":
    process_args(sys.argv[1:])
