#!/usr/bin/python#!/usr/bin/python
# -*- coding: utf-8 -*-

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
# Modified on 2014-04 for clustering support.
#


#
# USAGE for 10 nodes:
# python init_topology_cluster.py 10
#
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
import textwrap
import threading

#
#
#   CONSTANTS
#
#########################################

LOGGING_LEVEL = logging.DEBUG

MIN_VMX_ID = 110
MAX_VMX_ID = 400

POOL_PATH = "/var/lib/vz/images/workstationpool/"
POOL_MIN_SIZE = 10
POOL_MAX_SIZE = 30

VMX_TEMPLATE_DISK = "/var/lib/vz/images/templates/vmx.vmdk"
VMDISKS_PATH = "/var/lib/vz/images/"

#
#
#   ARGUMENTS HANDLING & LOGGING
#
#########################################

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

Logger = logging.getLogger('init_topology')
Logger.addHandler(consoleHandler)
Logger.setLevel(LOGGING_LEVEL)

try:
    if sys.argv[1].isdigit() and sys.argv[1] > 0:
        NB_WANTED_VMX = int(sys.argv[1])
    else:
        Logger.error("Wrong argument type, 1st arg must be positive digit. Exiting.")
        sys.exit(1)
except IndexError:
    Logger.error("No argument given. Exiting.")
    sys.exit(1)
    
#
#
#   FUNCTIONS
#
#########################################
    
#
# spawnCommand: Spawn a command on distant machine using sshpass program
#
def spawnCommand(_cmd, _hostname, _user='root', _password='s3cr3t'):
    cmd = "sshpass -p '%s' ssh -o StrictHostKeyChecking=no -o LogLevel=quiet -o UserKnownHostsFile=%s %s@%s '%s'" % (_password,os.devnull,_user,_hostname,_cmd)
    pipe = subprocess.Popen(cmd, bufsize=2048, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    streamdata = pipe.communicate()
    #[rc, stdout, stderr]
    return [pipe.returncode,streamdata[0],streamdata[1]]

#
#
#   CLASSES
#
#########################################

#
# ProxmoxNode: represent one Proxmox cluster node
#
class ProxmoxNode:

    def __init__ (self, _nodeId, _hostname):
        self.hostname = _hostname
        self.nodeId = _nodeId
        self.vmDictionary = {}
        
    #
    # updateVmDictionary: retreive virtual machines status and store it in self.vmDictionary
    #
    def updateVmDictionary(self):
        self.vmDictionary = {}
        res = spawnCommand('qm list', self.hostname)[1].strip().split('\n')
        if res != ['']:
            for line in res :
                Logger.debug(line)
                vm = line.split()
                if vm[0] != 'VMID':
                    self.vmDictionary[vm[0]] = vm[1:]
    
    #
    # getVmDictionary: update vmdictionary and return it 
    #    
    def getVmDictionary(self):
        self.updateVmDictionary()
        return self.vmDictionary
            
    
    #
    # getRunningVmxNb: return the number of running virtual machines called 'vmx' on this node
    #                    
    def getRunningVmxNb(self):
        nbVmx = 0
        for key,value in self.getVmDictionary().items():
            if value[0] == 'vmx' and value[1] == 'running':
                nbVmx += 1
        return nbVmx
    
    
    #
    # startVmx: start a virtual machine
    #
    def startVmx(self,_id):
        Logger.info('starting vm ' + _id)
        res = spawnCommand('qm start %s'%(str(_id)), self.hostname)
        Logger.debug(str(res))
    
    
    #
    # vmExists: return True when a vm with a specified id exists
    #
    def vmExists(self,_vmId):
        if str(_vmId) in self.getVmDictionary():
            return True
        return False
        

    
    #
    # findFreePoolID : returns a free pool ID (integer)
    #
    def findFreePoolID(self):
        res = spawnCommand('ls %s'%POOL_PATH, self.hostname)
        files = res[1].strip().split('\n')
        for id in range(1,9999):
            if str(id) not in files:
                return id    


    #
    # managePool : Manage the pool best availability of virtual machines
    #
    def managePool(self,_neededVM=0):
        
        Logger.debug('(%s) entering managePool'%self.hostname)
        Logger.info("(%s) Managing vm pool on "%self.hostname)
        
        res = spawnCommand('ls %s'%POOL_PATH, self.hostname)
        files = res[1].strip().split('\n')
        
        Logger.debug('(%s) Need to create %s vmx'%(self.hostname,str(_neededVM)))
        Logger.debug("(%s) Content of pool before adjustment (%d files) = %s" %(self.hostname,len(files),str(files)))
        
        # Handle overload
        if (POOL_MIN_SIZE < _neededVM) and (len(files) < _neededVM):
            Logger.info("(%s) There is a pool overload of %s virtual machines, correcting... (may take some time)"%(self.hostname,str(_neededVM-len(files))))
            overload = _neededVM-len(files)
            for i in range(overload):
                id = self.findFreePoolID()
                dest = os.path.join(POOL_PATH,str(id))
                res = spawnCommand('cp %s %s'%(VMX_TEMPLATE_DISK,dest), self.hostname)
            Logger.info("(%s) Done."%(self.hostname))
        
        # Adjust up
        elif len(files) < POOL_MIN_SIZE:
            Logger.info("(%s) Adjusting vm pool over it's minimal level, please wait..."%(self.hostname))
            for i in range(len(files), POOL_MIN_SIZE):
                id = self.findFreePoolID()
                dest = os.path.join(POOL_PATH,str(id))
                res = spawnCommand('cp %s %s'%(VMX_TEMPLATE_DISK,dest), self.hostname)
            Logger.info("(%s) Done."%(self.hostname))
        
        # Adjust down (if no overload)
        elif len(files) > POOL_MAX_SIZE:
            Logger.info("(%s) Adjusting vm pool under it's maximal level, please wait..."%(self.hostname))
            
            for i in range(POOL_MAX_SIZE, len(files)):        
                res = spawnCommand('ls %s'%POOL_PATH, self.hostname)
                files = res[1].strip().split('\n')
                Logger.debug("(%s) files %s"%(self.hostname,str(files)))
                
                rmfile = os.path.join(POOL_PATH,files[0])
                Logger.debug("(%s) Removing %s"%(self.hostname,rmfile))
                spawnCommand('rm %s'%rmfile, self.hostname)
                
                time.sleep(0.5)
                
            Logger.info("(%s) Done."%(self.hostname))
        
        res = spawnCommand('ls %s'%POOL_PATH, self.hostname)
        files = res[1].strip().split('\n')
        Logger.debug("(%s) Content of pool after adjustment = %s" %(self.hostname,str(files)))

        Logger.debug('(%s) leaving managePool'%self.hostname)
        

    #
    # createVm: create a virtual machine with specified id
    #        
    def createVm(self,_vmId):
        
        Logger.debug('(%s) entering createVm'%self.hostname)
        
        res = spawnCommand('ls %s'%POOL_PATH, self.hostname)
        files = res[1].strip().split('\n')
        
        srcFile = os.path.join(POOL_PATH,files[0])
        destDir = os.path.join(VMDISKS_PATH,str(_vmId))
        destFile = os.path.join(VMDISKS_PATH,str(_vmId),"disk.vmdk")
        
        res = spawnCommand('mkdir %s'%destDir, self.hostname)
        if res[0] != 0:
            spawnCommand('rm -rf %s'%destDir, self.hostname)
            spawnCommand('mkdir %s'%destDir, self.hostname)
        
        Logger.debug("(%s) Moving file %s to %s"%(self.hostname,srcFile,destFile))
        spawnCommand('mv %s %s'%(srcFile,destFile), self.hostname)
        
        qmCreateCmd = "qm create %s -name vmx -memory 128 -socket 1 -core 1 -keyboard fr -ostype l26 -vga std -net0 virtio,bridge=vmbr0 -net1 virtio,bridge=vmbr3 -virtio0 local:%s/disk.vmdk,size=5G -bootdisk virtio0"%(_vmId,_vmId)
        Logger.debug('(%s) qmCreateCmd = %s'%(self.hostname,qmCreateCmd))
        res = spawnCommand(qmCreateCmd, self.hostname)
        
        if res[0] == 0:
            Logger.info(" -> Success.")
        else:
            Logger.error(' -> Error : ' + str(res))
            
        spawnCommand('qm start %s'%(_vmId), self.hostname)
        
        Logger.debug('(%s) leaving createVm'%self.hostname)

    #
    # safeDeleteVm: delete a vm safely
    #
    def safeDeleteVm(self,_vmId):
        # stop vm
        Logger.debug('(%s) Stoping vmx id = %s'%(self.hostname,_vmId))
        spawnCommand('qm stop %s'%(_vmId), self.hostname)
        
        # move disk back to pool
        srcFile = os.path.join(VMDISKS_PATH,str(_vmId),"disk.vmdk")
        destFile = os.path.join(POOL_PATH,str(self.findFreePoolID()))
        res = spawnCommand('mv %s %s '%(srcFile,destFile), self.hostname)
        
        if res[0] != 0:
            Logger.warning("there's no disk to delete, ignoring.")
        
        # delete directory
        diskDir = os.path.join(VMDISKS_PATH,str(_vmId))
        spawnCommand('rm -rf %s'%diskDir, self.hostname)
        
        if res[0] != 0:
            Logger.warning("there's no disk directory to delete, ignoring.")
        
        # delete vm
        Logger.debug('(%s) deleting vmx id = %s'%(self.hostname,_vmId))
        res = spawnCommand('qm destroy %s -skiplock 1'%(str(_vmId)), self.hostname)
        
        if res[0] != 0:
            Logger.error('Could not destroy vm %s '%str(_vmId))
        else:
            while self.vmExists(_vmId):
                time.sleep(1)
    
#
# ProxmoxCluster: represents the full Proxmox cluster
#    
class ProxmoxCluster:

    def __init__ (self):        
        self.pxNodes = []

        for pxInfo in self.getClusterMembers():
            Logger.debug('Creating pxNode %s hostname %s'%(pxInfo[0],pxInfo[1]))
            self.pxNodes.append(ProxmoxNode(pxInfo[0],pxInfo[1]))
            
        for pxNode in self.pxNodes:
            pxNode.updateVmDictionary()


    #
    # getClusterMembers: return a list of Proxmox nodes using the template : [[nodeId,hostname],[nodeId,hostname],...]
    #
    def getClusterMembers(self):
        members = []
        res = spawnCommand('pvecm nodes', '127.0.0.1')[1].strip().split('\n')
        for line in res :
            node = line.split()
            if node[0] != 'Node':
                members.append([node[0],node[5]])
        return members
        

    #
    # initTopology: Initialize topology for the whole cluster (main function)
    #
    def initTopology(self,_nbWantedVmx):
        runningVmxNb = 0
        for pxNode in self.pxNodes:
            runningVmxNb += pxNode.getRunningVmxNb()
            
        Logger.debug('>> running vmx (total) = ' + str(runningVmxNb))
        
        if runningVmxNb > _nbWantedVmx:
            Logger.info('Too much vmx, correcting...')
            self.deleteVmx(runningVmxNb-_nbWantedVmx)
            Logger.info("Topology initialized")
            
        elif runningVmxNb < _nbWantedVmx:
            Logger.info('Not enough vmx, correcting...')
            
            # Finds how many vmx each node needs to create
            nbNeedCreate = _nbWantedVmx - runningVmxNb
            
            needVmDic = {}
            loadList = {}
            for px in self.pxNodes:
                loadList[px.hostname] = len(px.getVmDictionary())
                needVmDic[px.hostname] = 0
                
            for i in range(nbNeedCreate):
                pxNode = None
                for px in self.pxNodes:
                    if px.hostname == min(loadList, key=loadList.get):
                        pxNode = px
                loadList[pxNode.hostname] += 1
                needVmDic[pxNode.hostname] += 1         
            
            Logger.debug('needVmDic = ' + str(needVmDic))
            #raw_input("Press Enter to continue...")
            
            # Manage vm pool according to needVmDic
            threadList = []
            for pxNode in self.pxNodes:
                threadList.append(threading.Thread( target=pxNode.managePool,  args=[needVmDic[pxNode.hostname]+1] ))
            for t in threadList:
                t.start()
            for t in threadList:
                t.join()
            Logger.debug("threads finished")
                
            # Start or create vmx
            self.startOrCreateVmx(_nbWantedVmx-runningVmxNb)
            Logger.info("Topology initialized")
            
        else:
            Logger.info('Right number of vmx, exiting...')            
            print 'TOPO SUCCESS'
            sys.exit(0)
    
    
    #
    # getMaxLoadedNode: returns the most loaded Proxmox node
    #
    def getMaxLoadedNode(self):
        loadList = {}
        for px in self.pxNodes:
            loadList[px.hostname] = len(px.getVmDictionary())
            pxNode = None
            for px in self.pxNodes:
                if px.hostname == max(loadList, key=loadList.get):
                    pxNode = px
            return pxNode
                    
    #
    # startOrCreateVmx: creates _nb vmx on cluster or starts existing machines if needed 
    #              
    def startOrCreateVmx(self,_nb):
        Logger.debug('entering createVmx')
        
        loadList = {}
        for px in self.pxNodes:
            loadList[px.hostname] = len(px.getVmDictionary())
        Logger.debug('loadList = ' + str(loadList))
        
        # find and start stopped vmx
        for px in self.pxNodes:
            for key,value in sorted(px.getVmDictionary().items()):
                if value[0] == 'vmx' and value[1] == 'stopped' and _nb > 0:
                    px.startVmx(key)
                    _nb -= 1
        
        #creating vmx
        if _nb > 0:
            Logger.info('Creating %d vmx'%_nb)
            
            # create list of used vmx ids
            vmxIds = []
            for px in self.pxNodes:
                vmxIds += px.getVmDictionary().keys()
            Logger.debug('vmxIds = '+str(vmxIds))
                
            for i in range(_nb):
                pxNode = None
                for px in self.pxNodes:
                    if px.hostname == min(loadList, key=loadList.get):
                        pxNode = px
                Logger.debug('least loaded pxNode = ' + str(pxNode.hostname))
                loadList[pxNode.hostname] += 1
                
                # find free spot in vmxIds
                newVmxId = ''
                for i in xrange(MIN_VMX_ID,MAX_VMX_ID+1):
                    if str(i) not in vmxIds:
                        newVmxId = str(i)
                        vmxIds += [newVmxId]
                        break
                        
                Logger.info('(%s) Creating vmx %s...'%(pxNode.hostname,newVmxId))
                pxNode.createVm(newVmxId)                
                
            Logger.debug('leaving createVmx')
    
    
    #
    # deleteVmx: deletes _nb vmx
    #
    def deleteVmx(self,_nb):
        Logger.debug('entering deleteVmx')
        Logger.info('deleting %d vmx'%_nb)
        
        loadList = {}
        for px in self.pxNodes:
            loadList[px.hostname] = len(px.getVmDictionary())
        Logger.debug('loadList = ' + str(loadList))
        
        for i in range(_nb):
            pxNode = None
            for px in self.pxNodes:
                if px.hostname == max(loadList, key=loadList.get):
                    pxNode = px
            Logger.debug('Most loaded pxNode = ' + str(pxNode.hostname))
            
            loadList[pxNode.hostname] -= 1
            
            # find max vmxId
            maxId = 0
            for id,value in pxNode.getVmDictionary().items():
                if value[0] == 'vmx' and int(id) > maxId:
                    maxId = int(id)
            
            if maxId == 0:
                Logger.error('Cluster node %s has no more vmx to delete, exit program.'%pxNode.hostname)
                sys.exit(1)
            
            Logger.debug('(%s) Max vmx id = %s'%(pxNode.hostname,maxId))
            
            pxNode.safeDeleteVm(maxId)
            
        Logger.debug('leaving deleteVmx')


#
#
#   SCRIPT
#
#########################################    
Logger.debug(sys.argv)

# builds the cluster object
cluster = ProxmoxCluster()

# intialize topology for this cluster
cluster.initTopology(NB_WANTED_VMX)
            
print 'TOPO SUCCESS'
