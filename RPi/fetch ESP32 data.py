# -*- coding: utf-8 -*-
'''
Created on Mon Jan 14 16:41:05 2021

@author: Vojtěch Pluskal

To do if needed:
    save current time & repair
'''


import serial, time
from os import getcwd

serial_port = 'COM7'
#serial_port = '/dev/ttyUSB0'


print('Press Ctrl+C to stop.')
print('Cwd is: ' + getcwd())
#open serial port; The default is 8 data bits, no parity, one stop bit. (https://www.arduino.cc/reference/en/language/functions/communication/serial/begin/) 
ser = serial.Serial(
    port = serial_port,
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1
)

ser.set_buffer_size(rx_size = 2147483647, tx_size = 2147483647)

print('Opened serial port:', ser.name) #check which port was really used

data_file = open('data.txt', mode = 'w')
        
print('Start date and time =', time.ctime(time.time()))
try:
    ser.write('1'.encode())
    time.sleep(1)
    while(ser.read(inWaiting) > 0):
        serial_input = serial_input.decode().strip('\r\n') #convert to string from binary and remove \r\n
        data_file.write(str(serial_input))
                
except KeyboardInterrupt:
    print('>> Ctrl+C pressed, stopped.')
    ser.close()
    data_file.close()
    print('Stop date and time =', time.ctime(time.time()))
    raise SystemExit

print('Done!')
