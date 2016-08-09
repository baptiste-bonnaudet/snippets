#!/usr/bin/python

#
# ******************************************************
#     INFRASTRUCTURE INPUT FOR VERIFICATION TEST BED
# ******************************************************
#
# This script will generate a configuration file for
# the verification test bed STAX scenarios according to
# the arguments given. By defaul it will be executed
# after init-topology.py within a Jenkins job.
#
# Created on 11.07.2013
# Author: Baptiste BONNAUDET
#


#
#
#   IMPORTS
#
#########################################

import os
import sys
import time
import subprocess
import logging

#
#
#   CONSTANTS
#
#########################################

DEVNULL = open(os.devnull, 'wb')
LOGGING_LEVEL = logging.DEBUG


#
#
#   ARGUMENTS HANDLING & LOGGING
#
#########################################

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

logger = logging.getLogger('infrastructure-input')
logger.addHandler(consoleHandler)
logger.setLevel(LOGGING_LEVEL)

#
#
#   FUNCTIONS
#
#########################################

'''
getVmArray : returns an array of all virtual machines.
'''
def getVmArray():

        # creating array of vm, each vm is like :
        # [vmID,  name,             status,    maxMemorySize,  maxDiskSize,  PID]
        # ['108', 'server.flexnet', 'running', '512',          '1.00',       '2149']

        qmListPipe = subprocess.Popen("qm list", bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

        vmList = []
        for line in qmListPipe.stdout.readlines() :
                if line.split()[0].isdigit():
                        vmList.append(line.split())

        return vmList


'''
getVmIdArray returns an array of all virtual machines IDs.
'''
def getVmIdArray():
        idList = []
        vmList = getVmArray()
        for item in vmList:
                idList.append(item[0])
        return idList

'''
isRunning : returns True it the machine specified is running
'''
def isRunning(_vmID):
	vmList = getVmArray()
	for item in vmList:
		if item[0] == str(_vmID):
			if item[2] == "running":
				return True
	return False

'''
shutdownAllVM : Lists all virtual machines a shut them down.
'''
def shutdownAllVM():
	logger.info("Shutting down all virtual machines")
	
	idList = getVmIdArray()
	ok = False

	for vmID in idList:
		shutdownVM(vmID)
	while not ok:
		time.sleep(1)
		ok = True
		for vmID in idList:
			if isRunning(vmID):
				ok = False
	logger.info("Done")

'''
shutdownVM : shutdowns the specified virtual machine
'''
def shutdownVM(_vmID):
	logger.info("Shutting down virtual machine : "+_vmID)
	cmd = "qm shutdown "+_vmID+" -forceStop 1 -skiplock 1"
	qmStopPipe = subprocess.Popen(cmd, bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=DEVNULL, stderr=DEVNULL, close_fds=True)

'''
shutdownHosts : Shutdown physical hosts
'''
def shutdownHosts():
	logger.info("Shutting down host")
	os.system("halt")
	logger.info("Done")


#
#
#   SCRIPT
#
#########################################

logger.info("~~EXECUTING BENCH SHUTDOWN SCRIPT~~")

shutdownAllVM()

#shutdownHosts()

