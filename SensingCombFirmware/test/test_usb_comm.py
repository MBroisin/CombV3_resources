import os
import time
import numpy as np
import io
import datetime

import serial
from serial.tools import list_ports


port = ''
serial_connected = False
FUNC_FAILED = 1
FUNC_SUCCESS = 0
NEW_RECEIVED_LINE = '> '

OVERHEAD_SIZE = 7
NB_SAMPLES = 48
NB_SAMPLES_8 = 2*NB_SAMPLES
USB_COUNT = 1
PACK_SIZE = (NB_SAMPLES_8+OVERHEAD_SIZE)
DATA_SIZE =  (PACK_SIZE*USB_COUNT)
LED_DATA_SIZE = 9

G = 9.81
ACCEL_RANGE = 4*G
AXES = ['X', 'Y', 'Z']

f_handle = None
file_opened = False

def open_file(file_name='log.txt', cf=True):
    global f_handle
    global file_opened

    # defaults - assume did not work, until shown evidence..
    file_opened = False

    print("[I] working with file {}".format(file_name))

    if file_name == None :
        if cf:
            # check first whether directory exists?
            file_name = 'log_exp.txt'
            print("[I] Setting file name to : {}".format(file_name))
        else:
            print("   File not specified and creation not authorized")
            print("   The results won't be saved")
            return file_opened
    elif not(file_name[-4:]=='.txt'):
        print("   Output file should be a .txt file")
        print("   The results won't be saved")
        return file_opened
    elif os.path.isfile(file_name):
        print("   File found successfully")
    else :
        if not(cf):
            print("   File not found with path : " + file_name)
            print("   The results won't be saved")
            return file_opened

    try :
        f_handle = io.open(file_name, mode='a')
    except OSError as e:
        print("[E] File cannot be opened - error '{}'".format(e))
        return file_opened

    print("   File opened succssfully")
    print("   The results will be saved in " + file_name)
    file_opened = True
    return file_opened

def close_file():
    global f_handle
    global file_opened

    if file_opened:
        f_handle.close()
        file_opened = False
        print("File closed")
    else :
        print("File already closed")


def lookup_Nano33IoT_port(portspec="2341:8057", verbose=True):
    '''
    look for a unique device that matches the portspec.
    return device path string, or None in case of failure

    If there are no matches or multiple matches, raise RuntimeError.
    '''

    ret_path = None

    hits = list(list_ports.grep(portspec)) # cast generator to list so can check length
    if len(hits) == 1:
        # exactly one - proceed
        h = hits[0]
        ret_path = h.device
        if verbose:
            print('   [I] Nano board matched: using device={}'.format(ret_path))
        if not os.path.exists(ret_path):
            print("   [F] Nano board found but path failed! {}".format(h.device))
    elif len(hits) == 0:
        print("   [F] Nano board not found. Is it attached? check lsusb and dmesg")
    elif len(hits) > 1:
        print("   [E] MULTIPLE Nano boards found! ")
        for i, h in enumerate(hits):
            print("   device {}:".format(i))
            for pr in ['device', 'hwid', 'description', 'vid', 'hid', 'manufacturer', 'location']:
                val = h.__getattribute__(pr)
                print("\t{:20}: {}".format(pr, val))
            print("-- -- -- -- --")

    else:
        print("   [F] UNO board not found. and I cant count")

    return ret_path

def lookup_UNO_port(portspec="1A86:7523", verbose=True):
    '''
    look for a unique device that matches the portspec.
    return device path string, or None in case of failure

    If there are no matches or multiple matches, raise RuntimeError.
    '''

    ret_path = None

    hits = list(list_ports.grep(portspec)) # cast generator to list so can check length
    if len(hits) == 1:
        # exactly one - proceed
        h = hits[0]
        ret_path = h.device
        if verbose:
            print('   [I] UNO board matched: using device={}'.format(ret_path))
        if not os.path.exists(ret_path):
            print("   [F] UNO board found but path failed! {}".format(h.device))
    elif len(hits) == 0:
        print("   [F] UNO board not found. Is it attached? check lsusb and dmesg")
    elif len(hits) > 1:
        print("   [E] MULTIPLE UNO boards found! ")
        for i, h in enumerate(hits):
            print("   device {}:".format(i))
            for pr in ['device', 'hwid', 'description', 'vid', 'hid', 'manufacturer', 'location']:
                val = h.__getattribute__(pr)
                print("\t{:20}: {}".format(pr, val))
            print("-- -- -- -- --")

    else:
        print("   [F] UNO board not found. and I cant count")

    return ret_path

def connect_serial(device_path):
    """ 
    This functions connects to the specified serial port
    :params device_path: the address of the serial port
    :return status:
    """
    global port
    global serial_connected

    if(not serial_connected):
        try:
            print('Connecting to port {}'.format(device_path))
            port = serial.Serial(device_path, timeout=0.1, baudrate=57600)
            serial_connected = True
        except:
            print('Cannot connect to the device')
            serial_connected = False
            return FUNC_FAILED

    print('Connected')
    return FUNC_SUCCESS

def disconnect_serial():
    """ 
    This functions disconnects rom the serial port
    :params: -
    :return: -
    """
    global port
    global serial_connected

    if(not serial_connected):
        print('Already disconnected')
    else:
        port.close()
        serial_connected = False
        print('Disconnected')
        
def send_command(command, echo=False):
    """ 
    This functions sends a specific command to
    the connected serial port
    :params command: the command to be sent
    :return: -
    """
    
    if(echo == True):
        print('Sent :',command)

    # A command should finish by a return, otherwise nothing happens
    command += '\r\n'
    # We send the command character by character with a small delay
    # because some UART to USB bridges could miss one if sent to quickly
    if serial_connected == True:
        for char in command:
            port.write(char.encode('utf-8'))
            time.sleep(0.001)
    else :
        print('Serial port not defined yet. Quitting')

def receive_text(echo):
    rcv = bytearray([])

    # We read until the end of the transmission found by searching
    # the beginning of a new command line "ch> " from the Shell
    while(True):
        rcv += port.read()
        if(rcv[-2:] == b'\r\n'):
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
            print("{}".format(line))

    return text_lines

def receive_data(echo):
    rcv = bytearray([])

    # We read until the end of the transmission found by searching
    # the beginning of a new command line "ch> " from the Shell
    while(True):
        rcv += port.read()
        if(rcv[-2:] == b'\r\n'):
            break
    # Converts the bytearray into a string
    # text_rcv = rcv.decode("utf-8")
    # Splits the strings into lines as we would see them on a terminal
    text_lines = rcv.split(b'\r\n')

    # print([len(line) for line in text_lines])
    ret_text_lines = [line for line in text_lines if (len(line) in [DATA_SIZE, LED_DATA_SIZE])]

    if(echo == True):
        i = 0
        print('Received:')
        for line in ret_text_lines:
            i += 1
            print("{}".format(line))

    return ret_text_lines

def init_serial_port():
    """ 
    This functions initialize the connection with the 
    vibration generation module
    :params: -
    :return: -
    """
    global port, serial_connected
    sport = lookup_Nano33IoT_port()
    if sport is not None:
        connect_serial(sport)
        send_command('\n')
        print('Connected to ' + sport)
        return
    port = ''
    serial_connected = False
    
def decode_acc_values(data_array):
    int_values = [ord(samp) for samp in data_array.decode('latin-1')]

    for packID in range(USB_COUNT):
        pack_values = int_values[packID*PACK_SIZE:(packID+1)*PACK_SIZE]
        float_values = [0.235]*NB_SAMPLES

        accID = (pack_values[0] >> 4)
        axisID = (pack_values[0] & 3)
        print("Acc {} ({}) : ".format(accID, AXES[axisID]), end='')

        sampling_frequency = (2**(pack_values[1]-10))*800
        nb_samples_taken = pack_values[2]
        time_stamp = (pack_values[3] << 24) + (pack_values[4] << 16) + (pack_values[5] << 8) + pack_values[6]
        for i in range(OVERHEAD_SIZE, PACK_SIZE, 2):
            # temp = ((~((pack_values[i] << 8) | pack_values[i+1])) + 1) ^ (1 << 15)
            temp = ((pack_values[i+1] << 8) | pack_values[i])
            #print(temp>>15)
            #print(-(temp-65535*(temp>>15))*4*9.81/(65535))
            temp = -(temp-65535*(temp>>15))
            #temp = ((int_values[i] << 8) | int_values[i+1])
            #float_values[int(i/2)-OVERHEAD_SIZE] = (temp+32767)*ACCEL_RANGE/65535
            float_values[int((i-OVERHEAD_SIZE)/2)] = temp*ACCEL_RANGE/65535
            #print(float_values[int(i/2)-OVERHEAD_SIZE])
        print(np.around(np.array(float_values),2))
        print("(t = {} ms)".format(time_stamp/1000))
        data_to_write = np.around(np.array(float_values),4)
        f_handle.write("<DATA> (t={}, a={}, d={}, f={}, p={}) : ".format(time_stamp/1000, accID, AXES[axisID], sampling_frequency, nb_samples_taken))
        f_handle.write(np.array2string(data_to_write, separator=',', max_line_width=1000000))
        f_handle.write("\n")

def decode_led_status(led_array):
    values = [ord(samp) for samp in led_array.decode('latin-1')]

    board = int((values[0] == 255)) + 1
    time_stamp = (values[1] << 24) + (values[2] << 16) + (values[3] << 8) + values[4]

    print("Board {} leds : ".format(board), end='')

    led_status = values[5:]
    
    print(np.array(led_status))
    print("(t = {} ms)".format(time_stamp/1000))
    data_to_write = np.array(led_status)
    f_handle.write("<LEDS> (t={}, b={}) : ".format(time_stamp/1000, board))
    f_handle.write(np.array2string(data_to_write, separator=',', max_line_width=1000000))
    f_handle.write("\n")

init_serial_port()

# for i in range(10):
#     send_command('\r1\r\n')
#     time.sleep(0.5)
#     receive_text(echo=True)
#     send_command('\r0\r\n')
#     time.sleep(0.5)
#     receive_text(echo=True)

open_file()

if file_opened:
    t = time.time()
    now = datetime.datetime.now()
    f_handle.write("<INFO> (): Experiment started at {} t={} \r\n".format(now, t))

try:
    while True:
        tl = receive_data(echo=False)

        if (len(tl)>0):
            if (len(tl[0]) == LED_DATA_SIZE):
                print('coucou')
                decode_led_status(tl[0])
            else :
                decode_acc_values(tl[0])
except KeyboardInterrupt:
    pass

if file_opened:
    t = time.time()
    now = datetime.datetime.now()
    f_handle.write("<INFO> (): Experiment stopped at {} t={} \r\n".format(now, t))

disconnect_serial()
print('Quitting...')