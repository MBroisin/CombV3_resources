# Uploading firmware to SAMD devices

From the command line we can distribute code, using the tool bossac.

The version used in arduino studio and in platformio seems to be 1.7.0.

The tool should be compiled for the right architecture (of the host doing the
transfer, e.g. laptop, RPi, etc), and with this we can distribute a
cross-compiled binary firmware. 

## Procedure:

1. compile binaries in standard development environment
2. copy the .bin file (no need for .elf, .hex etc) to RPi in the field
3. use bossac to upload new firmware, with the following sequence:
   `stty -F /dev/ttyACM0 1200; sleep 1; bossa-1.7.0/bin/bossac --port=/dev/ttyACM0 --force_usb_port=true -e -w -v -b <full-path-to/firmware.bin> -R`
4. verify upload successful :)

## Tools in this directory

Precompiled binaries for arm7 and arm64 OS, v1.7.0 and v1.9.1.


