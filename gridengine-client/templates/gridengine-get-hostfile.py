#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging

def main():
    # parse args
    parser = argparse.ArgumentParser(description='get hostsfile for MPI')
    parser.add_argument('PE_HOSTFILE',
                        help='PE_HOSTFILE in SGE')
    parser.add_argument('OUTPUT',
                        nargs='?',
                        help='output file')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-o', '--openmpi',
                       action='store_true')
    group.add_argument('-m', '--mpich',
                       action='store_true')
    parser.add_argument('-D', '--debug',
                        action='store_true',
                        default=False)
    args = parser.parse_args()
    
    # setting
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    PE_HOSTFILE = args.PE_HOSTFILE
    output_type = None
    if args.openmpi:
        output_type = 'OpenMPI'
    elif args.mpich:
        output_type = 'MPICH'
    output = None
    if args.OUTPUT:
        output = args.OUTPUT

    contents = get_machinefile(PE_HOSTFILE, output_type)
    if output:
        fileout = open(output, 'w')
        fileout.write(contents)
        fileout.close()
    else:
        print(contents)
    

def get_machinefile(path, output_type):
    answer = ''
    logging.debug('open file: {}'.format(path))
    f = open(path, 'r')
    for line in f:
        words = line.split()
        host = words[0]
        proc = words[1]
        if output_type == 'OpenMPI':
            answer += '{host} slots={proc}\n'.format(host=host, proc=proc)
        elif output_type == 'MPICH':
            answer += '{host}:{proc}\n'.format(host=host, proc=proc)
        else:
            logging.error('unknown output_type: {}'.format(output_type))
            sys.exit(255)
    f.close()
    return answer

    
if __name__ == '__main__':
    main()
