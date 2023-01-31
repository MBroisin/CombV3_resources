import os
import numpy
import matplotlib
import matplotlib.pyplot
import io

import scipy
import scipy.ndimage
import scipy.stats

NB_ILEDS_TOT    = 6
NB_ILEDS_B      = [4, 2]
LED_COLORS      = [':r', ':b', ':g', ':m', ':k', ':y']

def cut_string_between(string, begin_mark, end_mark):
    #print((string.split(begin_mark)[1]))
    return (string.split(begin_mark)[1]).split(end_mark)[0]

def extract_data(dat, rem_data=[]):
    
    SEQ_IDENTIFIER_BEG = '<'
    SEQ_IDENTIFIER_END = '>'
    PAR_IDENTIFIER_BEG = '('
    PAR_IDENTIFIER_END = ')'
    DAT_IDENTIFIER_BEG = '['
    DAT_IDENTIFIER_END = ']'
    
    output_data = dict.fromkeys(range(1,11))
    accel_format = ['X', 'Y', 'Z']
    axis_format = ['val', 't']

    output_data['ileds'] = dict.fromkeys(range(1,7))
    output_data['vleds'] = dict.fromkeys(range(1,3))
    
    for okey in output_data.keys():
        if okey == 'ileds' or okey == 'vleds':
            for lkey in output_data[okey].keys():
                output_data[okey][lkey] = dict.fromkeys(axis_format)
                for tkey in output_data[okey][lkey].keys():
                    output_data[okey][lkey][tkey] = []
            continue
        output_data[okey] = dict.fromkeys(accel_format)
        for akey in output_data[okey].keys():
            output_data[okey][akey] = dict.fromkeys(axis_format)
            for axkey in output_data[okey][akey].keys():
                output_data[okey][akey][axkey] = []
            
   
    for i in range(0, len(data)):
        line = dat[i]
        
        if (line==''):
            continue
                
        begseq = cut_string_between(line, SEQ_IDENTIFIER_BEG, SEQ_IDENTIFIER_END)
        
        if (begseq == 'DATA'):
            params_string = cut_string_between(line, PAR_IDENTIFIER_BEG, PAR_IDENTIFIER_END)
            params_list = params_string.split(',')
            
            timestamp = float(params_list[0].split('=')[1])
            accel = int(params_list[1].split('=')[1])
            axis = params_list[2].split('=')[1]
            freq = int(params_list[3].split('=')[1])
            nb_datapoints = int(params_list[4].split('=')[1])

            # print('Accel n{}, axis = {}'.format(accel, axis))
            raw_data = cut_string_between(line, DAT_IDENTIFIER_BEG, DAT_IDENTIFIER_END)
            raw_data = raw_data.replace(' ', '')
            raw_data = [float(x) for x in raw_data.split(',')]
            
            timestamps = [timestamp + t/freq*1000 for t in range(nb_datapoints)]
            #print(timestamps)
            
            for index in rem_data:
                timestamps.pop(index)
                raw_data.pop(index)
            
            output_data[accel][axis]['val'] = output_data[accel][axis]['val'] + raw_data
            output_data[accel][axis]['t'] = output_data[accel][axis]['t'] + timestamps

        elif (begseq == 'LEDS'):
            params_string = cut_string_between(line, PAR_IDENTIFIER_BEG, PAR_IDENTIFIER_END)
            params_list = params_string.split(',')

            timestamp = float(params_list[0].split('=')[1])
            nb_board = int(params_list[1].split('=')[1])

            # print('Accel n{}, axis = {}'.format(accel, axis))
            raw_data = cut_string_between(line, DAT_IDENTIFIER_BEG, DAT_IDENTIFIER_END)
            raw_data = raw_data.replace(' ', '')
            raw_data = [int(x) for x in raw_data.split(',')]
            
            for ileds_i in range(NB_ILEDS_B[nb_board-1]):
                output_data['ileds'][(nb_board-1)*NB_ILEDS_B[0]+ileds_i+1]['val'].append(raw_data[ileds_i])
                output_data['ileds'][(nb_board-1)*NB_ILEDS_B[0]+ileds_i+1]['t'].append(timestamp)


    return output_data

def plot_accelerations(acc_data):
    N_max = -1
    for okey in acc_data.keys():
        if (okey == 'ileds' or okey == 'vleds'):
            matplotlib.pyplot.figure(figsize=(17, 8))
            for lkey in acc_data[okey].keys():
                if not(acc_data[okey][lkey]['t']==[]):
                    matplotlib.pyplot.plot(acc_data[okey][lkey]['t'][:N_max], acc_data[okey][lkey]['val'][:N_max], LED_COLORS[lkey-1], label='IR led'+str(lkey), drawstyle='steps-post')
            matplotlib.pyplot.title('Leds '+str(okey))
            matplotlib.pyplot.xlabel('time [ms]')
            matplotlib.pyplot.ylabel('leds level [-]')
            matplotlib.pyplot.legend()
            matplotlib.pyplot.savefig('plots/leds_'+str(okey))

        if not(isinstance(okey, int)):
            continue
            
        matplotlib.pyplot.figure(figsize=(17, 8))
        matplotlib.pyplot.plot(acc_data[okey]['X']['t'][:N_max], acc_data[okey]['X']['val'][:N_max], 'r', label='X')
        matplotlib.pyplot.plot(acc_data[okey]['Y']['t'][:N_max], acc_data[okey]['Y']['val'][:N_max], 'b', label='Y')
        matplotlib.pyplot.plot(acc_data[okey]['Z']['t'][:N_max], acc_data[okey]['Z']['val'][:N_max], 'g', label='Z')
        matplotlib.pyplot.grid()
        matplotlib.pyplot.ylim([-20, 20])
        
        matplotlib.pyplot.title('Acc '+str(okey))
        matplotlib.pyplot.xlabel('time [ms]')
        matplotlib.pyplot.ylabel('Acceleration [m/s^-2]')
        matplotlib.pyplot.legend()
        matplotlib.pyplot.savefig('plots/Acc'+str(okey))
        # matplotlib.pyplot.show()

filename = './log.txt'
log_file = io.open(filename, mode='r')
data = log_file.read().split('\n')
log_file.close()

raw_acc_data = extract_data(data)
plot_accelerations(raw_acc_data)