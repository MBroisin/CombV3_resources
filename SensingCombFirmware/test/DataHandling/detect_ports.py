import os

import serial
from serial.tools import list_ports
import json


NANO_PORT_SPEC = "2341:8057"

def lookup_Nano33IoT_port(portspec=NANO_PORT_SPEC, verbose=True):
    '''
    look for devices that matches the portspec.
    return list of device path strings, or None in case of failure

    If there are no matches or more than 2, raise RuntimeError.
    '''

    ret_path_list = None

    hits = list(list_ports.grep(portspec)) # cast generator to list so can check length
    if len(hits) == 1:
        # exactly one - proceed
        h = hits[0]
        ret_path_list = [h]
        if verbose:
            print('   [I] Board matched: using device={}'.format(ret_path_list))
    elif len(hits) == 0:
        print("   [F] Board not found. Is it attached? check lsusb and dmesg")
    elif len(hits) == 2:
        print("   [I] 2 boards found! ")
        # for i, h in enumerate(hits):
        #     #print([x[4:] for x in h.__getattribute__('hwid').split(' ') if x[:3]=='SER'])
        #     print("   device {} with short ID={}:".format(i, h.__getattribute__('hwid')))
        #     print("-- -- -- -- --")
        ret_path_list = hits
    elif len(hits)>2:
        print("   [E] Too many boards found! ")
        for i, h in enumerate(hits):
            print("   device {}:".format(i))
            for pr in ['device', 'hwid', 'description', 'vid', 'hid', 'manufacturer', 'location']:
                val = h.__getattribute__(pr)
                print("\t{:20}: {}".format(pr, val))
            print("-- -- -- -- --")

    else:
        print("   [F] UNO board not found. and I cant count")

    return ret_path_list

def discover_boards():
    devices = lookup_Nano33IoT_port()

    if devices is None:
        print('Did not find any boards or too many. Returning...')
        return
    
    f = open('./IDs.json')
    ids_list = json.load(f)
    f.close()

    ports = {}

    count_top = 0
    count_bottom = 0

    for device in devices:
        short_id = [x[4:] for x in device.__getattribute__('hwid').split(' ') if x[:3]=='SER'][0]
        
        if short_id in ids_list['top']:
            count_top += 1
            ports['top'] = {'device':device.device, 'connected':False, 'serial_port':None}
        elif short_id in ids_list['bottom']:
            count_bottom += 1
            ports['bottom'] = {'device':device.device, 'connected':False, 'serial_port':None}
        else :
            print("Found an unidentified board")

    if (count_top > 1 or count_bottom > 1):
        print('Multiple top or bottom boards found. Quitting')
        return None
    
    if (count_top == 0 and count_bottom == 0):
        print('No identified board found. Quitting')
        return None

    return ports

    
    
    

