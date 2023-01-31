import serial.tools.list_ports
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type=str, required=True)
args = parser.parse_args()

while True:
	ports_list = serial.tools.list_ports.comports()
	devices_list = [po.device for po in ports_list]
	if (args.port in devices_list):
		break
	time.sleep(1)
