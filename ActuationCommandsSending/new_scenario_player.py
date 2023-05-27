# File                : vibrational_comb.py
# Author             : Matthieu Broisin, modified by Martin S., modified by Matthieu B
# Creation date        : 17 July 2020
# Last modif date    : 06 September 2021
# version            : 3.0
# Brief                :

#import numpy as np
#import random
import serial
from serial.tools import list_ports
#import struct
#import sys
import sys
import time
import datetime as dt
#import os
import os.path
import io
#from subprocess import Popen, PIPE
import threading
import argparse
import json
import logging

parser = argparse.ArgumentParser()
parser.add_argument('--device_path', type=str, default=None, help='path of comb controller, leave unset for autolookup')
parser.add_argument('--file', type=str, required=True, help='required, filename for output file')
parser.add_argument('-sce', "--scenario_file", type=str, required=True, help="Path to scenario file to follow for sending commands")
parser.add_argument('-old', "--old_scenario", type=bool, required=False, default=None, help="Use the old version (numbered) of the scenario files (newer version with lists)")
args = parser.parse_args()

VERBOSE = True
VERBOSE_DATA = False
VERBOSE_THREAD = False

NEW_RECEIVED_LINE = '> '

FUNC_SUCCESS = True
FUNC_FAILED = False

NUMBER_OF_ACTS = 8

FREQ_STM32 = 160000000

# input possibilities
port = None
serial_connected = False
f_handle = None

file_opened = False

# helper funcs on coloured output
BLU     = '\033[94m'
WARN    = '\033[43;4;30m'
ENDC    = '\033[0m'
ERR     = '\033[41m'
GREENBG = '\033[37;42m' # nasty...

def cprint(msg, clr=BLU):
    print(clr + msg + ENDC)


def connect_serial():
    global port
    global serial_connected

    if(not serial_connected):
        try:
            print('Connecting to port {}'.format(args.device_path))
            port = serial.Serial(args.device_path, timeout=0.1)
            serial_connected = True
        except:
            print('Cannot connect to the device')
            serial_connected = False
            return FUNC_FAILED

    print('Connected')
    return FUNC_SUCCESS

def disconnect_serial():
    global port
    global serial_connected

    if(not serial_connected):
        print('Already disconnected')
    else:
        port.close()
        serial_connected = False
        print('Disconnected')


def flush_shell():
    # In case there was a communication problem
    # we send two return commands to trigger the sending of
    # a new command line from the Shell (to begin from the beginning)
    port.write(b'\r\n')
    port.write(b'\r\n')
    time.sleep(0.1)

    # Flushes the input (BUT BLOCKS)
    ret = []
    while(port.inWaiting()):
        ret.append(port.read())

    return ret


_ix = 0
def consume_once():
    global _ix
    # consume anything if something?
    if port.in_waiting:
        ret = receive_text(False)
        for line in ret:
            cprint(">>[D]{} |{}".format(_ix, line))
            f_handle.write(line)
    else:
        cprint("[D] nothing incoming {}".format(_ix))

    ix += 1


def send_command(command, echo=False, lf_handle=None):
    command = command.upper()
    if(echo == True):
        print('Sent :',command)

    # if lf_handle is not None:
    #     lf_handle.write("^{} ".format(command))
    #     print_time(verb=False)
    logging.info("Comm    : ^{} ".format(command))

    # A command should finish by a return, otherwise nothing happens
    command += '\r\n'
    # We send the command character by character with a small delay
    # because some UART to USB bridges could miss one if sent to quickly
    for char in command:
        port.write(char.encode('utf-8'))
        time.sleep(0.001)


def receive_text(echo):
    rcv = bytearray([])

    # We read until the end of the transmission found by searching
    # the beginning of a new command line "ch> " from the Shell
    while(True):
        rcv += port.read()
        if(rcv[-4:] == b'ch> '):
            break
    # Converts the bytearray into a string
    text_rcv = rcv.decode("utf-8")
    # Splits the strings into lines as we would see them on a terminal
    text_lines = text_rcv.split('\r\n')

    if(echo == True):
        i = 0
        print('Received:')
        for line in text_lines:
            i += 1
            print("{} {} {}".format(i, NEW_RECEIVED_LINE, line))

    return text_lines

def lookup_STM_port(portspec="5740"):
    '''
    look for a unique device that matches the portspec.
    return device path string, or None in case of failure

    If there are no matches or multiple matches, raise RuntimeError.
    '''

    ret_path = None

    hits = list(list_ports.grep("5740")) # cast generator to list so can check length
    if len(hits) == 1:
        # exactly one - proceed
        h = hits[0]
        ret_path = h.device
        print('   [I] STM board matched: using device={}'.format(ret_path))
        if not os.path.exists(ret_path):
            logging.warning("STMs    : Board found but path failed")
            raise RuntimeError("   [F] STM board found but path failed! {}".format(h.device))
    elif len(hits) == 0:
        logging.warning("STMs    : Board not found")
        raise RuntimeError("   [F] STM board not found. Is it attached? check lsusb and dmesg")
    elif len(hits) > 1:
        print("   [E] MULTIPLE STM boards found! ")
        for i, h in enumerate(hits):
            print("   device {}:".format(i))
            for pr in ['device', 'hwid', 'description', 'vid', 'hid', 'manufacturer', 'location']:
                val = h.__getattribute__(pr)
                print("\t{:20}: {}".format(pr, val))
            print("-- -- -- -- --")
        logging.warning("STMs    : MULTIPLE board found")
        raise RuntimeError("   [F] MULTIPLE STM boards found! Supply path with --device_path <path> or disconnect others.")
    else:
        logging.warning("STMs    : No board found")
        raise RuntimeError("   [F] STM board not found. andI cant count")

    return ret_path

def recv_rtc_response(verb=True):
    ''' return true if we found GETRTC in response. Optionally print all to stdout '''
    hit = None
    recv = receive_text(False)
    for line in recv:
        if line.startswith("#Current RTC value") or "Current RTC" in line:
            #hit = True
            hit = line
            if file_opened:
                f_handle.write(line + "\r\n")
        if verb or not file_opened:
            print("$[D]${}".format(line))
    return hit

def get_rtc_with_retries(ntry=3, verb=True):
    got = False
    n = 0

    while got is False:

        send_command('GETRTC', VERBOSE, lf_handle=f_handle)
        #print_time()
        recvd = recv_rtc_response(True)
        n += 1
        if recvd is None:
            msg = "[W]{} no RTC response ".format(n)
            cprint(msg, WARN)

        if recvd is not None:
            msg = "[I] RTC response found on {}th attempt: {}".format(n, recvd)
            cprint(msg, GREENBG)
            got = True
            break

        if n >= ntry:
            break
    return (got, n)

def cmd_trig_handler(t1, t2, delay):
    if (t1==11 and t2==11):
        cmd = 'stop_trig'
        send_command(cmd, VERBOSE, f_handle)
        time.sleep(delay)
        return
    cmd = 'trig {} {}'.format(t1, t2)
    send_command(cmd, VERBOSE, f_handle)
    time.sleep(delay)

def cmd_mux_handler(mux, val, delay):
    cmd = 'mux {} {}'.format(mux, val)
    send_command(cmd, VERBOSE, f_handle)
    time.sleep(delay)

def cmd_leds_handler(val, delay):
    cmd = 'leds {}'.format(val)
    send_command(cmd, VERBOSE, f_handle)
    time.sleep(delay)

def cmd_wait_handler(delay):
    time.sleep(delay)


###################              BEGINNING OF PROGRAMM               ###################
# SUMMARY OF THE EXPERIMENTS

# log initialization
strtime = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
log_fname = args.file + '.log'
format = "%(asctime)s: %(message)s"
logging.basicConfig(filename=log_fname, format=format, level=logging.INFO,
                        datefmt="%Y%m%dT%H%M%S")


logging.info("Main    : Scenario started")

experiment_lineup = dict()
if args.old_scenario:
    try :
        experiment_lineup = json.load(open(args.scenario_file))
    except:
        logging.error("Scen    : Unable to read scenario file")
        print('Unable to read scenario file. Quitting')
else :
    try :
        experiment_lineup_temp = json.load(open(args.scenario_file))
    except:
        logging.error("Scen    : Unable to read scenario file")
        print('Unable to read scenario file. Quitting')
    for idline, line in enumerate(experiment_lineup_temp):
        experiment_lineup[str(idline)] = line

for i in range(0, len(experiment_lineup)):
    print(experiment_lineup[str(i)])
print(experiment_lineup)
logging.info("Scen    : Scenario found > {}".format(experiment_lineup))

# LOOKUP the device
serial_port_given = False
if args.device_path is not None:
    serial_port_given = True
else:
    print('[I] NO DEVICE GIVEN, searching for device!')
    ser_path = lookup_STM_port(portspec="5740")
    if ser_path is not None:  # it raises an exception in all other cases anyway.
        serial_port_given = True
        args.device_path = ser_path
        logging.info("STMs    : Board found")




TEST = False
EXPERIMENT = not(TEST)

if(serial_port_given):

    # print("TRY TO OPEN FILE")
    # ret = open_file()
    # print("   [I] open success?", ret)


    ## Do something here
    connect_serial()
    time.sleep(0.25)
    #print("TRY to clear 1")
    #consume_once()
    print("TRY to flush ")
    mess = flush_shell()
    print("   flush done ({} by read)".format(len(mess)))
    time.sleep(0.1)

    # if file_opened:
    #     f_handle.write('\r\n')
    #     f_handle.write('\r\n')
    #     f_handle.write('###########################################################################################')
    #     f_handle.write("^Beginning of the experiment : ")
    #     print_time()

    print("[D] looking for RTC.")
    (got_rtc, n) = get_rtc_with_retries(15)
    print("    RTC {} after {} retries.".format(got_rtc, n) )

    if EXPERIMENT:
        for i in range(0, len(experiment_lineup)):

            # Make space in the log file
            # if file_opened:
            #     f_handle.write('\r\n')
            #     f_handle.write('\r\n')

            # Send corresponding command and sleep
            if experiment_lineup[str(i)][0] == 'trig':
                cmd_trig_handler(
                    experiment_lineup[str(i)][1],
                    experiment_lineup[str(i)][2],
                    experiment_lineup[str(i)][3]
                )
            elif experiment_lineup[str(i)][0] == 'mux':
                cmd_mux_handler(
                    experiment_lineup[str(i)][1],
                    experiment_lineup[str(i)][2],
                    experiment_lineup[str(i)][3]
                )
            elif experiment_lineup[str(i)][0] == 'leds':
                cmd_leds_handler(
                    experiment_lineup[str(i)][1],
                    experiment_lineup[str(i)][2]
                )
            elif experiment_lineup[str(i)][0] == 'wait':
                cmd_wait_handler(
                    experiment_lineup[str(i)][1]
                )
            else : 
                print('Unvalid command, skipping')
                continue

            # if file_opened:
            #     f_handle.write('\r\n')
            #     f_handle.write('\r\n')
                        

        time.sleep(1)
        cmd = 'stop_trig'
        send_command(cmd, VERBOSE, f_handle)
        '''
        if file_opened:
            f_handle.write(cmd.upper())
        
        print_time()
        '''


        # NOTE (RM): when I use reset, the listener thread has problems
        #cmd  = 'reset'
        #send_command(cmd, VERBOSE, f_handle)
        #f_handle.write(cmd.upper())
        # if file_opened:
        #     f_handle.write('END : ')
        # print_time()

# close_file()

disconnect_serial()
logging.info("Main    : Scenario stopped")
