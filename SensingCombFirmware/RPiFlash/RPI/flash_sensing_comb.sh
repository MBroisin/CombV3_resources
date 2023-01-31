#!/bin/bash

for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
    (
        syspath="${sysdevpath%/dev}"
        devname="$(udevadm info -q name -p $syspath)"
        
        if [[ "$devname" != "tty"* ]]
        then 
		exit
		fi
		
		#echo "$devname"
		eval "$(udevadm info -q property --export -p $syspath)"
		#echo "$(udevadm info -q property --export -p $syspath)"
		
		if [[ "$ID_MODEL" == "Arduino_NANO_33_IoT" ]]
        then 
			echo "##################"
			echo "Found Arduino Nano 33 IoT with ID $ID_SERIAL_SHORT"
			#set -x
			firmware1="$(grep $ID_SERIAL_SHORT IDs.txt | grep -o "board1.bin")"
			firmware2="$(grep $ID_SERIAL_SHORT IDs.txt | grep -o "board2.bin")"
			firmware3="$(grep $ID_SERIAL_SHORT IDs.txt | grep -o "test_blink200ms.bin")"
			firmware4="$(grep $ID_SERIAL_SHORT IDs.txt | grep -o "test_blink1000ms.bin")"
			firmware="./../PC/bins/$firmware1$firmware2$firmware3$firmware4"
			echo "$firmware"
			#set +x
			if [[ "$firmware" != *".bin" ]]
			then 
				echo "Unvalid firmware"
				exit
			fi
			
			#set -x
			flash_tool="bossac/bossa-1.7.0/armv7l-5.10.17/bin/bossac"
			cmd_boot="$(stty -F /dev/$devname 1200; sleep 1)"
			echo "Board in bootloader mode. Waiting for port to reset..."
			cmd_wait="$(python3 serial_port_check.py -p /dev/$devname)"
			echo "Port found. Flashing..."
			echo cmd_flash="$($flash_tool --port=/dev/$devname --force_usb_port=true -e -w -v -b $firmware -R)"
			x=$?
			echo "Code finished with exit code $x"
			#set +x
			exit
		fi
		
		if [[ "$ID_MODEL" == "Arduino_NONA_WLAN" ]]
        then 
			echo "##################"
			echo "Found Damaged Arduino Nano 33 IoT"
			echo "Fixing ..."
			
			firmware="./../PC/bins/test_blink200ms.bin"
		 	
			flash_tool="bossac/bossa-1.7.0/armv7l-5.10.17/bin/bossac"
			cmd_boot="$(stty -F /dev/$devname 1200; sleep 1)"
			cmd_wait="$(python3 serial_port_check.py -p /dev/$devname)"
			echo cmd_flash="$($flash_tool --port=/dev/$devname --force_usb_port=true -e -w -v -b $firmware -R)"
			x=$?
			echo "Code finished with exit code $x"
			exit
		fi
		        
	)
done
