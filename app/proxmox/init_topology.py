#!/usr/bin/python#!/usr/bin/python

#
# ******************************************************
#        INIT TOPOLOGY FOR VERIFICATION TEST BED
# ******************************************************
#
# This script will configure the verification test bed
# for use of virtual machines. It will generate the needed
# VMs from a pool of template VMs. If the pool is not big
# enought it will take more time depending on your system.
#
# Created on 07.07.2013
# Author: Baptiste BONNAUDET
#


#
#
#   IMPORTS
#
#########################################

import os
import sys
import subprocess
import shutil
import time
import logging.handlers

#
#
#   CONSTANTS
#
#########################################


NB_NODES = 0

MIN_WORKSTATION_ID = 110
MAX_WORKSTATION_ID = 400

VMDISKS_PATH = "/var/lib/vz/images/"
WORKSTATION_TEMPLATE_DISK = "/var/lib/vz/images/templates/vmx.vmdk"

POOL_PATH = "/var/lib/vz/images/workstationpool/"
POOL_MIN_SIZE = 3
POOL_MAX_SIZE = 20

LOGGING_LEVEL = logging.INFO

DEVNULL = open(os.devnull, 'wb')

GET_NB_VMX = False

#
#
#   ARGUMENTS HANDLING & LOGGING
#
#########################################

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

logger = logging.getLogger('init_topology')
logger.addHandler(consoleHandler)
logger.setLevel(LOGGING_LEVEL)


try:
    if sys.argv[1] == "getNbOfRunningVmx":
        GET_NB_VMX = True
    elif sys.argv[1].isdigit() and sys.argv[1] > 0:
        NB_NODES = int(sys.argv[1])
    else:
        logger.error("Wrong argument type, must be positive digit. Exiting.")
        sys.exit(1)
except IndexError:
    logger.error("No argument given. Exiting.")
    sys.exit(1)


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
getVmIdArray : returns an array of all virtual machines IDs.
'''
def getVmIdArray():
        idList = []
	vmList = getVmArray()
        for item in vmList:
                idList.append(item[0])
	return idList

'''
isRunning : check if a virtual machine is running
'''
def isRunning(_vmID):
        vmList = getVmArray()
        for item in vmList:
                if item[0] == str(_vmID):
                        if item[2] == "running":
                                return True
        return False

'''
exists : test if the specified virtual machine exists
'''
def exists(_vmID):
	vmList = getVmArray()
	for item in vmList:
                if item[0] == str(_vmID):
			return True
	return False

'''
getWorkstations : returns an arrayd of all workstations
'''
def getWorkstations():
	return [x for x in getVmArray() if (int(x[0]) >= MIN_WORKSTATION_ID) and int(x[0]) <= MAX_WORKSTATION_ID]

'''
getRunningWorkstations : returns an arrayd of running workstations
'''
def getRunningWorkstations():
    vmxList = getWorkstations()
    runningVmxList = []
    for vm in vmxList:
        if isRunning(vm[0]):
            runningVmxList.append(vm)
    return runningVmxList

'''
findFreeSpot : returns a free vmID
'''
def findFreeSpot(_vmList, _min, _max, _exclude=[]):
	idList = []
	for item in _vmList:
		idList.append(item[0])

	for id in range(_min, _max):
		if (str(id) not in idList) and (id not in _exclude):
			return id
	logger.error("No more space in specified range. Exiting.")
	sys.exit(1)

'''
createVMs : create a certain number of virtual machines given in parameter
'''
def createVMs(_nbVM):
	achieved = []
	
	for i in range(_nbVM):
		id = findFreeSpot(workstationList, MIN_WORKSTATION_ID, MAX_WORKSTATION_ID,achieved)
		try:
			logger.info("Creating virtual machine " + str(id))

		        # Move vm disk from pool to new VM
			files = [f for f in os.listdir(POOL_PATH) if os.path.isfile(os.path.join(POOL_PATH,f))]

			srcFile = os.path.join(POOL_PATH,files[0])
			destDir = os.path.join(VMDISKS_PATH,str(id))
			destFile = os.path.join(VMDISKS_PATH,str(id),"disk.vmdk")

			logger.debug("Creating directory : "+destDir)
		
			try:
				os.mkdir(destDir)
			except OSError :
				shutil.rmtree(destDir)
				os.mkdir(destDir)

			logger.debug("Moving file "+srcFile+" to "+destFile)
			shutil.move(srcFile,destFile)
		
			# Create new VM configuration file
	
			qmCreateCmd = "qm create "+str(id)+" -name vmx -memory 128 -socket 1 -core 1 -keyboard fr -ostype l26 -vga std -net0 virtio,bridge=vmbr0 -net1 virtio,bridge=vmbr3 -virtio0 local:"+str(id)+"/disk.vmdk,size=5G -bootdisk virtio0"
	
			qmCreatePipe = subprocess.Popen(qmCreateCmd, bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
			qmCreatePipe.wait()
	
			achieved.append(id)

			logger.info(" -> Success.")

		except:
			logger.error(" -> Can't create virtual machine.")
	return 0

'''
findFreePoolID : returns a free pool ID (integer)
'''
def findFreePoolID():
	files = [f for f in os.listdir(POOL_PATH) if os.path.isfile(os.path.join(POOL_PATH,f))]
	for id in range(1,9999):
		if str(id) not in files:
			return id

'''
managePool : Manage the pool best availability of virtual machines
'''
def managePool(_neededVM=0):
	
        files = [f for f in os.listdir(POOL_PATH) if os.path.isfile(os.path.join(POOL_PATH,f))]
	
	logger.debug("Content of pool before adjustment = " + str(files))

        # Handle overload
        if (POOL_MIN_SIZE < _neededVM) and (len(files) < _neededVM):
                logger.info("There is a pool overload of "+str(_neededVM-POOL_MIN_SIZE)+" virtual machines, correcting...")
                overload = _neededVM-len(files)
                for i in range(overload):
                        id = findFreePoolID()
                        dest = os.path.join(POOL_PATH,str(id))
                        shutil.copyfile(WORKSTATION_TEMPLATE_DISK, dest)
                logger.info("Done.")

	# Adjust up
	elif len(files) < POOL_MIN_SIZE:
		logger.info("Adjusting vm pool over it's minimal level, please wait...")
		for i in range(len(files), POOL_MIN_SIZE):
                        id = findFreePoolID()
                        dest = os.path.join(POOL_PATH,str(id))
                        shutil.copyfile(WORKSTATION_TEMPLATE_DISK, dest)
		logger.info("Done.")

	# Adjust down (if no overload)
	elif len(files) > POOL_MAX_SIZE:
		logger.info("Adjusting vm pool under it's maximal level, please wait...")
		for i in range(POOL_MAX_SIZE, len([f for f in os.listdir(POOL_PATH) if os.path.isfile(os.path.join(POOL_PATH,f))])):
			files = [f for f in os.listdir(POOL_PATH) if os.path.isfile(os.path.join(POOL_PATH,f))]
			os.remove(os.path.join(POOL_PATH,files[0]))
		logger.info("Done.")

        files = [f for f in os.listdir(POOL_PATH) if os.path.isfile(os.path.join(POOL_PATH,f))]
        logger.debug("Content of pool after adjustment = " + str(files))


'''
stopVM : stop a virtual machine
'''
def stopVM(_vmID):
	logger.info("Stoping virtual machine : " + _vmID)
	cmd = "qm shutdown "+_vmID+" -forceStop 1 -skiplock 1"
	qmStopPipe = subprocess.Popen(cmd, bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=DEVNULL, stderr=DEVNULL, close_fds=True)

	while isRunning(_vmID):
		time.sleep(1)


'''
deleteVM : delete a virtual machine
'''
def deleteVM(_vmID):
	logger.info("Deleting virtual machine : " + _vmID)

	try:
		diskDir = os.path.join(VMDISKS_PATH,str(_vmID))
		shutil.rmtree(diskDir)
	except IOError:
                logger.warning("There's no disk directory to delete, ignoring")

	cmd = "qm destroy "+_vmID+" -skiplock 1"
	qmDestroyPipe = subprocess.Popen(cmd, bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=DEVNULL, stderr=DEVNULL, close_fds=True)

	while exists(_vmID):
                time.sleep(1)

'''
moveDiskBackToPool : move a virtual disk back to the pool
'''
def moveDiskBackToPool(_vmID):
	try:
		srcFile = os.path.join(VMDISKS_PATH,str(_vmID),"disk.vmdk")
        	destFile = os.path.join(POOL_PATH,str(findFreePoolID()))
		shutil.move(srcFile,destFile)
	except IOError:
		logger.warning("there's no disk to delete, ignoring.")

'''
safeDeleteVM : delete a VM safely
'''
def safeDeleteVM(_vmID):
        stopVM(_vmID)
        moveDiskBackToPool(_vmID)
        deleteVM(_vmID)

#
#
#   SCRIPT
#
#########################################


workstationList = getWorkstations()

if GET_NB_VMX:
    print "Running=" + str(len(getRunningWorkstations()))
    sys.exit(0)

logger.info("~~EXECUTING BENCH TOPOLOGY INITIALIZATION SCRIPT~~")

# Manage VM number

logger.info("Number of nodes selected :"+str(NB_NODES))

if (len(workstationList) < NB_NODES): 		#Not enought vm
	logger.info("Not enought workstations, creating "+str(NB_NODES-len(workstationList))+" new ones")
	neededVmNb = NB_NODES-len(workstationList)
	managePool(neededVmNb)
	createVMs(neededVmNb)

elif (len(workstationList) > NB_NODES): 	#Too much vm
	exeedingNb = len(workstationList)-NB_NODES
	logger.info("Too much workstations, deleting "+str(exeedingNb))
	idList = []
        for item in workstationList:
                idList.append(item[0])
	del idList[:(len(idList)-exeedingNb)]
	
	for vmID in idList:
		safeDeleteVM(vmID)
		
else:
	logger.info("There's already the correct number of workstations created : "+str(len(workstationList)))

# Start all VMs

logger.info("Starting all virtual machines")
idList = getVmIdArray()
for vmID in idList:
 	cmd = "qm start "+vmID
	qmStartPipe = subprocess.Popen(cmd, bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=DEVNULL, stderr=DEVNULL, close_fds=True)

logger.info("Topology initialized")

print 'OK'

sys.exit(0)
