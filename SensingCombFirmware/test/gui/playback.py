'''
Aim: read data from a file, pass down some channel periodically
'''

import time
import argparse
import numpy as np

#{{{ data parsing
DAT_IDENTIFIER_BEG = '['
DAT_IDENTIFIER_END = ']'
SEQ_IDENTIFIER_BEG = '<'
SEQ_IDENTIFIER_END = '>'
PAR_IDENTIFIER_BEG = '('
PAR_IDENTIFIER_END = ')'

def parse_hdr(line):
    params_string = cut_string_between(line, PAR_IDENTIFIER_BEG, PAR_IDENTIFIER_END)
    if not len(params_string):
        return {'accel': -1}
    params_list = params_string.split(',')

    #print(params_list)

    timestamp = float(params_list[0].split('=')[1])
    accel = int(params_list[1].split('=')[1])
    axis = params_list[2].split('=')[1]
    freq = int(params_list[3].split('=')[1])
    nb_datapoints = int(params_list[4].split('=')[1])

    hdr = {
        'timestamp': timestamp,
        'accel': accel,
        'axis': axis,
    }
    return hdr

def parseline(line):
    # sometimes, we have a mangling of DATA and INFO lines. We could clean up
    # in the log file, or be robust to them here.
    l = line.strip()
    #print(l)
    parts = l.split(':')
    hdr = parse_hdr(line)

    dtype = begseq = cut_string_between(line, SEQ_IDENTIFIER_BEG, SEQ_IDENTIFIER_END)
    if dtype == "DATA":
        # check whether we have data identifiers
        if not (DAT_IDENTIFIER_BEG in parts[1] and DAT_IDENTIFIER_END in parts[1]):
            raw_data = []
        else:
            try:
                raw_data = cut_string_between(parts[1], DAT_IDENTIFIER_BEG, DAT_IDENTIFIER_END)
            except IndexError as e:
                print(f"[E] with line |{line}| got error {e}")
            raw_data = raw_data.replace(' ', '')
            raw_data = [float(x) for x in raw_data.split(',')]

    else:
        raw_data = []

    raw = np.array(raw_data)
    return dtype, hdr, raw

def cut_string_between(string, begin_mark, end_mark):
    #print((string.split(begin_mark)[1]))
    return (string.split(begin_mark)[1]).split(end_mark)[0]
# }}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verb', action='store_true')
    parser.add_argument('-p', '--port', type=str, default="/dev/pts/5")
    parser.add_argument('-i', '--infile', type=str, default=None)
    parser.add_argument('-n', '--num', type=int, default=4)
    parser.add_argument('--protocol', type=int, default=2, 
            help='simplified data tx, or resend entire data row')
    parser.add_argument('-r', '--row', type=str, choices=['top', 'bottom'], default='top')
    parser.add_argument('-d', '--delay', type=float, default=0.1)
    args = parser.parse_args()

    t0 = time.time()
    #raw = serial.Serial(args.port, BAUD, timeout=0.1)
    i = 0
    tgt_accel = 3
    if args.row == 'top':
        tgt_accel_list = [6,7,8,9,10]
    elif args.row == 'bottom':
        tgt_accel_list = [1,2,3,4,5]

    with open(args.infile) as f:
        for line in f:
            if not len(line):
                continue
            dty, hdr, raw = parseline(line)
            #print(f"[I] {i:03} {dty:6} {len(raw)}")
            t1 = time.time()

            if dty == 'DATA':
                if not hdr['accel'] in tgt_accel_list: # tgt_accel:
                    #print(f"[I] {hdr['accel']} does not match. skip")
                    continue
                # push down the test channe;

                with open(args.port, "w") as pipe:
                    # simplified data format (just emit 5 samples)
                    if args.protocol == 1:
                        d = ",".join([f"{x:4.4f}" for x in raw[:4]])
                        s = f"{t1-t0:.1f} {i:05} {hdr['accel']} {d}"
                    else: # protocol
                        s = line.strip()

                    pipe.write(s + "\n")

            time.sleep(args.delay)

            i += 1
            if i > args.num:
                break

