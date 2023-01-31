import serial
import time

FUNC_FAILED = 1
FUNC_SUCCESS = 0

def connect_serial(port_dict):
    """ 
    This functions connects to the specified serial port
    :params device_path: the address of the serial port
    :return status:
    """

    if not(port_dict['connected']):
        try:
            print('Connecting to port {}'.format(port_dict['device']))
            port_dict['serial_port'] = serial.Serial(port_dict['device'], timeout=0.1, baudrate=57600)
            port_dict['connected'] = True
        except:
            print('Cannot connect to the device')
            port_dict['connected'] = False
            return port_dict

    print('Device {} connected'.format(port_dict['device']))
    return port_dict

def disconnect_serial(port_dict):
    """ 
    This functions disconnects rom the serial port
    :params: -
    :return: -
    """

    if not(port_dict['connected']):
        print('Already disconnected')
        return port_dict
    else:
        port_dict['serial_port'].close()
        port_dict['connected'] = False
        print('Device {} disconnected'.format(port_dict['device']))
        return port_dict
        
def send_command(port_dict, command, echo=False):
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
    if port_dict['connected'] == True:
        for char in command:
            port_dict['serial_port'].write(char.encode('utf-8'))
            time.sleep(0.001)
    else :
        print('Serial port not defined yet. Quitting')

def receive_text(port_dict, echo=True):
    rcv = bytearray([])

    if not(port_dict['connected']):
        print('Cannot read from undefined serial port. Quitting')
        return
    # We read until the end of the transmission found by searching
    # the beginning of a new command line "ch> " from the Shell
    while(True):
        rcv += port_dict['serial_port'].read()
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

def receive_data(port_dict, accepted_data_sizes=None, echo=True):
    rcv = bytearray([])

    if not(port_dict['connected']):
        print('Cannot read from undefined serial port. Quitting')
        return
    # We read until the end of the transmission found by searching
    # the beginning of a new command line "ch> " from the Shell
    while(True):
        rcv += port_dict['serial_port'].read()
        if(rcv[-2:] == b'\r\n'):
            break
    # Converts the bytearray into a string
    # text_rcv = rcv.decode("utf-8")
    # Splits the strings into lines as we would see them on a terminal
    text_lines = rcv.split(b'\r\n')

    # print([len(line) for line in text_lines])
    if not(accepted_data_sizes is None):
        ret_text_lines = [line for line in text_lines if (len(line) in accepted_data_sizes)]
    else :        
        ret_text_lines = [line for line in text_lines]

    if(echo == True):
        i = 0
        print('Received:')
        for line in ret_text_lines:
            i += 1
            print("{}".format(line))

    return ret_text_lines
