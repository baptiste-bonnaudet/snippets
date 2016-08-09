#!/bin/bash

# KVM copier, copy a vitrual machine n times
# 
# Author : Baptiste BONAUDET
#
# HOW TO:
# bash vmcopy.sh --no-prompt vmID nbCopy
# bash vmcopy.sh vmID nbCopy
# 
# The --no-prompt option : no user prompt for input
#
# This script was made for older version of Proxmox which were missing the clone function


IFS='
'
noPrompt=0;

#
# FUNCTIONS
################################################

#Diep
#
#Die program prints an error message on std and in log file, then exit ; takes a string and an exit value as parameters
function diep
{
	echo "[ERROR] $1";
	echo "[`date`] $1 ; exited with value : $2" >> "`pwd`/$0.log";
	exit $2;
# HOW TO :
# diep "there's an error" 1
}

#DecToHex
#
#Convert decimal to hexadecimal ; takes an integer in the range 0-255 as parameter
function decToHex
{
	if (( $1 > 255 || $1 < 0 ))
	then 
		diep "Parameter > 255 or < 0 : $1" 4;
	else
		echo `echo "ibase=10;obase=16;$1" | bc`;
	fi
}

#GenerateMac
#
#Generate a random mac address
function generateMac
{
	#WARNING : This function does not work with systems like Proxmox because of their mac address specific range

	MAC=`(date; cat /proc/interrupts) | md5sum | sed -r 's/^(.{12}).*$/\1/; s/([0-9a-f]{2})/\1:/g; s/:$//;'`; #full mac address
	MAC=`echo $MAC | tr '[:lower:]' '[:upper:]'`	#to upper case
	
	echo $MAC;	
}


#GenerateMacWithID
#
#Generate a random mac address with a node ID ; takes an integer in the range 0-255 as parameter
function generateMacWithID
{
	if (( $1 > 255 || $1 < 0 ))
	then 
		diep "Parameter > 255 or < 0 : $1" 4;
	else
		hex=$(decToHex $1);

		if (( ${#hex} < 2 ))
		then
			hex="0$hex";
		fi

		echo "12:86:E1:E9:AA:${hex}"
	fi
}

#Inquire
#
#Ask the user for yes or no answer
function inquire 
{
	echo  -n "$1 [$2/$3]?";
	read answer;

	finish="-1";
	while [ "$finish" = '-1' ]
	do
		finish="1";
		if [ "$answer" = '' ]
		then
			answer="";
		else
			case $answer in
			y | Y | yes | YES ) return 0;;
			n | N | no | NO ) return 1;;
			*) finish="-1";
			echo -n 'Invalid response -- please reenter:';
			read answer;;
			esac
		fi
	done

# HOW TO USE :
#inquire "Delete now ?" "y" "n"
#if (( $? == 0 ))
#then
#	echo "yesss"
#elif (( $? == 1 ))
#then
#	echo "noooo"
#fi
}

#
# CHECKING
################################################

#check if sudoer
if (( $UID != 0 ))
then
	echo -e "Please run this script with sudo:\nsudo bash $0 $@";
	exit 1;
fi




#check number of parameters

if (( $# < 2 || $# > 3 ))
then
	diep "Expecting 2 or 3 parameters not $#" 1;
else
	if (( $# == 2 ))
	then
		vmID=$1;
		NbCpy=$2;
	elif (( $# == 3 ))
	then
		if [ "$1" == "--no-prompt" ]
		then
			noPrompt=1;
			vmID=$2;
			NbCpy=$3;
		else
			diep "Wrong parameters : $@" 1;
		fi
	fi
fi

#Correct number

idMax=$vmID+$NbCpy

if (( $idMax > 255 || $idMax < 0 ))
then 
	diep "Number of copies and vmID > 255 or < 0 : $idMax" 4;
fi

#Try to find VM conf

if [[ ! ( -e /etc/pve/qemu-server/$vmID.conf ) ]] 
then 
	#can't access file
	diep "Can't access the file /etc/pve/qemu-server/$vmID.conf" 2
fi

#Try to find VM disk
declare -a files=(`ls /var/lib/vz/images/$vmID/*.vmdk`);

if (( ${#files[*]} == 0 )) 
then 
	#can't access file
	diep "No vmdk file in /var/lib/vz/images/$vmID/" 3;
else
	vmDisk="${files[0]}";
fi


#
# PROGRAM
################################################
clear

echo -e " *******************************************";
echo -e "**        KVM Virtual Machine Copier       *";
echo -e "********************************************";
echo -e "*******************************************\n";

echo "Welcome to the KVM Virtual Machine Copier, everything looks fine and you are going to copy the virtual machine $vmID, $NbCpy times.";

if (( $noPrompt != 1 ))
then
	inquire "Do you want to proceed ?" "y" "n";

	if (( $? == 0 ))
	then
		echo -e "Proceeding...\n";
	elif (( $? == 1 ))
	then
		echo "Exit program.";
		exit 0;
	fi
fi

#is there a VM ID above $vmID ?

declare -a confFiles=(`ls /etc/pve/qemu-server/`);

for file in ${confFiles[*]}
do
	subStrId=${file:0:3};
	if (( $subStrId > $vmID &&  $subStrId <= $vmID+$NbCpy ))
	then
		if (( $noPrompt != 1 ))
		then
			echo "[WARNING] There's a VM ID above $vmID VM : $subStrId";
			inquire "Do you want to delete it ? (answering yes will delete /etc/pve/qemu-server/$file file)" "y" "n";
			if (( $? == 0 ))
			then
				echo -e "Proceeding...\n";
				rm -r -f /etc/pve/qemu-server/$file;
			elif (( $? == 1 ))
			then
				echo "Leaving program.";
				exit 0;
			fi
		else
				rm -r -f /etc/pve/qemu-server/$file;				
		fi
	fi
done

#cleaning the vm configuration
echo "> Cleaning the original configuration file";

file_upd8="/etc/pve/qemu-server/tmp.conf";

while read line
do
	if [ "${line:0:3}" == "net" ]
	then
		netID=${line:3:1} 			# 0

		echo ">> found network device id=$netID"

		pos=`echo $line | grep -b -o "vmbr" | awk 'BEGIN {FS=":"}{print $1}'` 		
		bridgeID=${line:$pos+4:1}		# 0

		macHW=$(generateMacWithID $vmID);

		echo "net${netID}: rtl8139=${macHW},bridge=vmbr${bridgeID}" >> $file_upd8;
	elif [ "${line:0:7}" == "virtio0" ]
	then
		pos=`echo $line | grep -b -o "size=" | awk 'BEGIN {FS=":"}{print $1}'`
		size=${line:$pos+5:1}			# 5
		echo ">> found virtio0, replacing disk name.";
		echo "virtio0: local:$vmID/vm-$vmID-disk-1.vmdk,size=${size}G" >> $file_upd8;
	else
		echo "$line" >> $file_upd8;
	fi
done < /etc/pve/qemu-server/$vmID.conf

mv /etc/pve/qemu-server/tmp.conf /etc/pve/qemu-server/$vmID.conf;
echo -e ">> done !\n";


#copy configuration file

declare -i newVmID=$vmID+1;

while (($newVmID <= ($vmID+$NbCpy)))
do
	echo "> Copying new vm configuration file for $newVmID";

	file_upd8="/etc/pve/qemu-server/$newVmID.conf";

	echo "" > $file_upd8;

	echo ">> copying configuration file /etc/pve/qemu-server/$newVmID.conf";

	while read line
	do
		if [ "${line:0:3}" == "net" ]
		then
			netID=${line:3:1} 			# 0

			echo ">> found network device id=$netID"

			pos=`echo $line | grep -b -o "vmbr" | awk 'BEGIN {FS=":"}{print $1}'` 		
			bridgeID=${line:$pos+4:1}		# 0

			macHW=$(generateMacWithID $vmID);

			echo "net${netID}: rtl8139=${macHW},bridge=vmbr${bridgeID}" >> $file_upd8;

			echo "net$netID: rtl8139=$macHW,bridge=vmbr$bridgeID" >> $file_upd8;
		elif [ "${line:0:7}" == "virtio0" ]
		then
			pos=`echo $line | grep -b -o "size=" | awk 'BEGIN {FS=":"}{print $1}'`
			size=${line:$pos+5:1}			# 5
			echo ">> found virtio0, replacing disk name.";
			echo "virtio0: local:$newVmID/vm-$newVmID-disk-1.vmdk,size=${size}G" >> $file_upd8;
		else
			echo "$line" >> $file_upd8;
		fi
	done < /etc/pve/qemu-server/$vmID.conf
	
	echo -e ">> done !\n";
	newVmID=$newVmID+1;
done

#copy vmdisk
declare -i newVmID=$vmID+1;

while (($newVmID <= ($vmID+$NbCpy)))
do
	echo "> Copying new vm disk file for $newVmID";
	echo ">> creating directory /var/lib/vz/images/$newVmID/";

	mkdir /var/lib/vz/images/$newVmID/ 2>/dev/null;

	if (( $? == 1 ))
	then
		if (( $noPrompt != 1 ))
		then
			echo ">>>[WARNING] directory /var/lib/vz/images/$newVmID/ already exists. Deleting dir and it's content...";
			inquire ">>>Do you want to proceed ? (answering yes will delete /var/lib/vz/images/$newVmID/ directory and all of its content)" "y" "n";
			if (( $? == 0 ))
			then
				echo ">>>Proceeding...";
				rm -r -f /var/lib/vz/images/$newVmID/;
				mkdir /var/lib/vz/images/$newVmID/;
			elif (( $? == 1 ))
			then
				echo ">>>Leaving program.";
				exit 0;
			fi
		else
			rm -r -f /var/lib/vz/images/$newVmID/;
			mkdir /var/lib/vz/images/$newVmID/;
		fi
	fi

	echo ">> copying new vm disk, please wait...";
	cp $vmDisk /var/lib/vz/images/$newVmID/vm-$newVmID-disk-1.vmdk;

	echo ">> done !";
	newVmID=$newVmID+1;
done


echo -e "\nKVM Virtual Machine Copier was successful, leaving program.";
exit 0;
