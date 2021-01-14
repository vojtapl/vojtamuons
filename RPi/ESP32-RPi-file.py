# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 14:28:01 2020

@author: Vojtěch Pluskal

Does not like restarting of ESP32!!!

To do:
    save time at start and at the end; how?
"""


import serial, time

#serial_port = "COM7"
serial_port = "/dev/ttyUSB0"


print("Press Ctrl+C to stop.")

#open serial port; The default is 8 data bits, no parity, one stop bit. (https://www.arduino.cc/reference/en/language/functions/communication/serial/begin/) 
ser = serial.Serial(
    port = serial_port,
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1
)

print("Opened serial port:", ser.name) #check which port was really used
        
data_file = open("data.txt", mode = "w")

print("Start date and time =", time.ctime(time.time()))
try:
    while True: #does it save?      
        serial_input = ser.readline()
        serial_input = serial_input.decode().strip("\r\n") #convert to string from binary and remove \r\n
        if(serial_input != ""):      
            time_now_epoch = time.time()
        
            if not str(serial_input).isdigit():
                print("Unsaved, non numeric input:", serial_input)
                print("Current date and time =", time.ctime(time_now_epoch))
                continue
                
            print(serial_input)
            print("Current date and time =", time.ctime(time_now_epoch))
        
            data_to_save = str(serial_input) + "," + str(time_now_epoch) + ","
            
except KeyboardInterrupt:
    print(">> Ctrl+C pressed, stopped.")
    ser.close()
    data_file.close()
    print("Stop date and time =", time.ctime(time.time()))
    raise SystemExit
