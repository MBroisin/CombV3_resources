import os
import io


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
    
def file_write(sometext):
    if file_opened:
        f_handle.write(sometext)
    else:
        print('No open file yet')
