#!/usr/bin/python
# -*- coding: utf-8 -*-
# inspiation source: https://gist.github.com/turbinenreiter/7898985

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

import numpy as np
import time
import serial
from collections import deque
import argparse
import struct

from playback import parseline


OVERHEAD_SIZE = 7
NB_SAMPLES = 48
NB_SAMPLES_8 = 2*NB_SAMPLES
USB_COUNT = 1
PACK_SIZE = (NB_SAMPLES_8+OVERHEAD_SIZE)
DATA_SIZE =  (PACK_SIZE*USB_COUNT)

G = 9.81
ACCEL_RANGE = 4*G
AXES = ['X', 'Y', 'Z']


#{{{ read one message - with timeout
def read_msg(ser, timeout=1):
    ''' read one entire message '''
    #global cnt
    #
    c = None
    m_start = False
    m_len_known = False
    m_end = False
    ml = None
    m_rx = 0
    buf = []
    cnt1 = 0
    cnt2 = 0

    t_start = time.time()
    # wait until we get a header message.
    while m_start is False:
        cnt2 += 1
        #cnt  += 1
        if (cnt2 % 100) == 0:
            #print(".", end="")
            t_now = time.time()
            elap = t_now - t_start
            if elap > timeout:
                #print("exit early, elap: {}. cnt:{}".format(elap, cnt2))#, end="")
                return (None, 0, b"")
        while ser.inWaiting() > 0:
            cnt1 += 1
            c = ser.read(1)
            if c in MSG_STARTS:
                m_start = True
                cur_mtype,  = struct.unpack(">B", c)
                #print("[DD] first symbol (start, after {}): {}".format(cnt1, cnt2//1000, c))
                break
            #else:
            #    print("[DD] first symbol: {}".format(c))
        # now we exit the header loop.
    while m_len_known is False:
        while ser.inWaiting() > 0:
            c = ser.read(1)
            ml,  = struct.unpack(">B", c)
            m_len_known = True
            break

    #print("[I] msg header read: {} {} (ty: {} {})".format(
    #    cur_mtype, ml, type(cur_mtype), type(ml)))

    # waiting for the rest of the data.
    while m_rx < ml: # while not m_end
        while ser.inWaiting() > 0:
            c = ser.read(1)
            buf.append(c) # let's keep all bytes that come in
            m_rx += 1
            if m_rx == ml:
                break


    return cur_mtype, ml, buf

#}}}

def _readline(ser):
    #eol = b'\r'
    eol = b'\n'
    leneol = len(eol)
    line = bytearray()
    while True:
        c = ser.read(1)
        if c:
            line += c
            if line[-leneol:] == eol:
                break
        else:
            break
    return bytes(line)

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verb', action='store_true')
parser.add_argument('-s', '--show_debug', action='store_true')
parser.add_argument('-p', '--port', type=str, default="/dev/ttyACM0")
parser.add_argument('-b', '--buflen', type=int, default=10)
parser.add_argument('-d', '--dispival', type=int, default=2)
parser.add_argument('-m', '--send_ival', type=int, default=400)
parser.add_argument('-f', '--n_fields', type=int, default=1)
parser.add_argument('--row', type=str, choices=['top', 'bottom'], default='top')
parser.add_argument('--protocol', type=int, default=2, 
    help='simplified data tx, or resend entire data row')
parser.add_argument('-r', '--ref', type=float, default=1000.0)
args = parser.parse_args()
BAUD = 115200
raw = serial.Serial(args.port, BAUD, timeout=0.1)

def line2dat(line):
    _ds = line.decode('utf-8').split()[-1]
    d = np.array([float(_) for _ in _ds.split(',')])
    return d

def line2hdr(line):
    hf = line.decode('utf-8').split()[0:-1]
    if not len(hf) == 3:
        return -1, -1, -1
    ix = int(hf[1])
    acc = int(hf[2])
    t = float(hf[0])

    return t, acc, ix

def decode_acc_values(data_array):
    int_values = [ord(samp) for samp in data_array.decode('latin-1')]

    res_str = ''
    for packID in range(USB_COUNT):
        pack_values = int_values[packID*PACK_SIZE:(packID+1)*PACK_SIZE]
        float_values = [0.235]*NB_SAMPLES

        accID = (pack_values[0] >> 4)
        axisID = (pack_values[0] & 3)

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
        data_to_write = np.around(np.array(float_values),4)
        res_str += "<DATA> (t={}, a={}, d={}, f={}, p={}) : ".format(time_stamp/1000, accID, AXES[axisID], sampling_frequency, nb_samples_taken)
        res_str += np.array2string(data_to_write, separator=',', max_line_width=1000000)
        res_str += "\n"   
    return res_str


    

app = QtGui.QApplication([])

p = pg.plot()
p.setWindowTitle('live plot from serial')
p.addLegend()
p.setYRange(-20, 20, padding=0)
if args.row == 'top':
    plot_accs = [6,7,8,9,10]
elif args.row == 'bottom':
    plot_accs = [1,2,3,4,5]
clrs = [ '#ff4d2e', '#ffb62e', '#007fff', '#ddeedd', '#bbbbbb' ]

curves = {}
for i, a in enumerate(plot_accs):
    curves[a] = p.plot(pen=clrs[i], name=f"a{a}")

#curves = [p.plot(pen='#ffb62e', name='z') ]
D = {}
for k in curves:
    D[k] = deque([], args.buflen)

count = 0

def update():
    global curves, D, count
    #global curves, dataz, count
    line = _readline(raw)
    if not line:
        return

    if args.protocol == 1:
        t, acc, _row = line2hdr(line)
        datarray = line2dat(line)

    elif args.protocol == 2:
        print(type(line))
        print(line)
        line = line.decode(encoding='utf-8')
        dty, hdr, datarray = parseline(line)

    elif args.protocol == 3:
        try :
            line = decode_acc_values(line)
        except Exception:
            return
        dty, hdr, datarray = parseline(line)

    else:
        raise RuntimeError("[F] no protocol match")

    #print(f"[I] {i:03} {dty:6} {len(raw)}")
    t1 = time.time()
    
    acc = hdr.get('accel', -1)
    
    if not dty == 'DATA':
        return
    else:
        if not acc in plot_accs: # tgt_accel:
            #print(f"[I] {hdr['accel']} does not match. skip")
            return
    # look up which of the curves the pen should be
    if acc in D:
        [D[acc].append(_d) for _d in datarray]

    count += len(datarray)

    #[dataz.append(_d) for _d in datarray]

    if count % args.dispival == 0:
        for i, acc in enumerate(D):
            xdata = np.array(D[acc], dtype="float64")
            curves[acc].setData(xdata)

        #i = 0
        #xdata = np.array(dataz, dtype='float64')
        #curves[i].setData(xdata)


    app.processEvents()

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


'''
try:
    while True:
        line = _readline(raw)
        if not line:
            continue

        d = line2dat(line)
        print(f"{len(d)}: {d.mean():.3f}")
except KeyboardInterrupt:
    print("Bye")
'''
