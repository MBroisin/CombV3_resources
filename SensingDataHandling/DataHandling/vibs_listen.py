import time
import numpy as np
import datetime

import detect_ports as DP
import serial_connection as SC
import file_handler as FH

import argparse

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

ACCEPTED_DATA_SIZES = [DATA_SIZE, LED_DATA_SIZE]

G = 9.81
ACCEL_RANGE = 4*G
AXES = ['X', 'Y', 'Z']

ACC_NUMBER = 10
check_flow_counts = [0]*ACC_NUMBER
check_flow_second = [0]*ACC_NUMBER
check_flow_last   = [0.0]*ACC_NUMBER

def check_data_flow(ts, freq, acc_id, axis_id, verbose=True):
    global check_flow_counts, check_flow_second

    if not(axis_id == 2):
        return

    ts_array = np.linspace(ts/1000000, ts/1000000+NB_SAMPLES/freq, NB_SAMPLES)
    # print(check_flow_second[acc_id-1])
    # print(ts_array)

    for ts_i in range(ts_array.shape[0]):
        current_ts = ts_array[ts_i]

        if not(check_flow_second[acc_id-1] == int(current_ts)):
            # print previous result, and reset
            check_flow_last[acc_id-1] = check_flow_counts[acc_id-1]/freq*100
            if verbose :
                print("Data received (last 1s) ", end='')
                for acc_i in range(ACC_NUMBER):
                    print("| [{}:{}%] ".format(acc_i+1, np.around(check_flow_last[acc_i],1)), end='')
                print("|                               \r", end='')
            check_flow_counts[acc_id-1] = 1
            check_flow_second[acc_id-1] = int(current_ts)
            pass
        else:  
            check_flow_counts[acc_id-1] += 1
    
def decode_acc_values(data_array):
    int_values = [ord(samp) for samp in data_array.decode('latin-1')]

    for packID in range(USB_COUNT):
        pack_values = int_values[packID*PACK_SIZE:(packID+1)*PACK_SIZE]
        float_values = [0.235]*NB_SAMPLES

        accID = (pack_values[0] >> 4)
        axisID = (pack_values[0] & 3)
        # print("Acc {} ({}) : ".format(accID, AXES[axisID]), end='')

        sampling_frequency = (2**(pack_values[1]-10))*800
        nb_samples_taken = pack_values[2]
        time_stamp = (pack_values[3] << 24) + (pack_values[4] << 16) + (pack_values[5] << 8) + pack_values[6]
        for i in range(OVERHEAD_SIZE, PACK_SIZE, 2):
            temp = ((pack_values[i+1] << 8) | pack_values[i])
            temp = -(temp-65535*(temp>>15))
            float_values[int((i-OVERHEAD_SIZE)/2)] = temp*ACCEL_RANGE/65535

        data_to_write = np.around(np.array(float_values),4)
        # print(np.around(np.array(float_values),2))
        # print("(t = {} ms)".format(time_stamp/1000))
        
        # check_data_flow(time_stamp, sampling_frequency, accID, axisID)

        FH.file_write("<DATA> (t={}, a={}, d={}, f={}, p={}) : ".format(time_stamp/1000, accID, AXES[axisID], sampling_frequency, nb_samples_taken))
        FH.file_write(np.array2string(data_to_write, separator=',', max_line_width=1000000))
        FH.file_write("\n")

def decode_led_status(led_array):
    values = [ord(samp) for samp in led_array.decode('latin-1')]

    board = int((values[0] == 255)) + 1
    time_stamp = (values[1] << 24) + (values[2] << 16) + (values[3] << 8) + values[4]

    # print("Board {} leds : ".format(board), end='')

    led_status = values[5:]
    
    # print(np.array(led_status))
    # print("(t = {} ms)".format(time_stamp/1000))
    data_to_write = np.array(led_status)
    FH.file_write("<LEDS> (t={}, b={}) : ".format(time_stamp/1000, board))
    FH.file_write(np.array2string(data_to_write, separator=',', max_line_width=1000000))
    FH.file_write("\n")

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--duration", type=int, help="Duration (in seconds) of the listening", required=True)
parser.add_argument("-f", "--filename", type=str, help="Name of the log file to output data to", required=True)
args = parser.parse_args()

FH.open_file(file_name=args.filename) # +'.txt')

ports = DP.discover_boards()

for port_id in ports.keys():
    ports[port_id] = SC.connect_serial(ports[port_id])

t = time.time()
now = datetime.datetime.now()
FH.file_write("<INFO> (): Experiment started at {} t={} \r\n".format(now, t))

start_time = time.time()  # remember when we started
while (time.time() - start_time) < args.duration:
    for port_id in ports.keys():

        tl = SC.receive_data(
            ports[port_id], 
            accepted_data_sizes=ACCEPTED_DATA_SIZES,
            echo=False,
        )

        if (len(tl)>0):
            if (len(tl[0]) == LED_DATA_SIZE):
                decode_led_status(tl[0])
            else :
                decode_acc_values(tl[0])
            
t = time.time()
now = datetime.datetime.now()
FH.file_write("<INFO> (): Experiment stopped at {} t={} \r\n".format(now, t))

print("")
FH.close_file()
for port_id in ports.keys():
    ports[port_id] = SC.disconnect_serial(ports[port_id])


print("")
