# -*- coding: utf-8 -*-
"""
Created on Created on Mon Jan  4 20:21:08 2021
Based on code last saved on Mon Jan  4 20:21:00 2021

@author: Vojtěch Pluskal
"""

import serial
import time

serial_port = "COM7" #"/dev/ttyUSB0"

print("Press Ctrl+C to stop.")

ser = serial.Serial(port = serial_port, baudrate = 115200, bytesize = 8) #timeout?
print("Opened serial port: " + ser.name) #check which port was really used

data_file = open("data.txt", mode = "w")
try:
    while True: #does it save?      
        serial_input = ser.readline()
        serial_input = serial_input.decode().strip("\r\n") #convert to string from binary and remove \r\n
        
        time_now_epoch = time.time()

        if not str(serial_input).isnumeric():
            print("Unsaved, non numeric input:", serial_input)
            print("Current date and time =", time.ctime(time_now_epoch))
            continue
        
        print(serial_input)
        print("Current date and time =", time.ctime(time_now_epoch))

        data_file.write(str(serial_input) + "," + str(time_now_epoch) + ",")
except KeyboardInterrupt:
    print(">> Ctrl+C pressed, stopped.")
    ser.close()
    data_file.close()
    raise SystemExit
