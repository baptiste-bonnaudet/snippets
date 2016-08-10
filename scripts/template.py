#!/usr/bin/python
# coding: utf-8

# Desc:
#
# Usage: ./template.py -i "ls -l"
#
# Author: Baptiste Bonnaudet
###############################################

import os, sys, shutil, argparse, subprocess, logging.handlers

# const
LOGGING_LEVEL = logging.DEBUG

# handle command line arguments
parser = argparse.ArgumentParser(description='This script does...')
parser.add_argument('-i', metavar='input-var', help='this options does...')
parser.add_argument('--flag', action='store_true', help='this flag does...') # will store true if set

args = parser.parse_args()

# handle mendatory arguments
if args.i is None:
        print 'Missing argument, exiting...'
        sys.exit()

# hangle flags
if args.flag is True:
	pass

# logger format
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

# logger
log = logging.getLogger('init_topology')
log.addHandler(consoleHandler)
log.setLevel(LOGGING_LEVEL)


# spawn a command to the system, can be used with sshpass
def spawnCommand(_cmd):
    pipe = subprocess.Popen(_cmd, bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    streamdata = pipe.communicate()
    return [pipe.returncode,streamdata[0],streamdata[1]]


# example
res = spawnCommand(args.i)
log.debug('return code is:\n' + str(res[0]))
log.info('stdout is:\n' + str(res[1]))
log.error('stderr is:\n' + str(res[2]))
log.warning("this is a warning log")



