# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 14:28:01 2020

@author: Vojtěch Pluskal

Does not like restarting of ESP32!!!

To do:
    add time at start and at the end
"""


import serial, time
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# serial_port = "COM7"
serial_port = "/dev/ttyUSB0"


print("Press Ctrl+C to stop.")

#two line Google auth
gauth = GoogleAuth()
gauth.LocalWebserverAuth() #Creates local webserver and auto handles authentication.

#make Google Drive instance with Authenticated GoogleAuth instance
drive = GoogleDrive(gauth)

#get list of files on Google Drive
file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

for file in file_list:
    print("title: %s, id: %s" % (file["title"],file["id"]))
    if file["title"] == "miony_data.txt":
        print("Successfully opened Google Drive!")
        
        #open serial port
        ser = serial.Serial(port = serial_port, baudrate = 115200, bytesize = 8) #timeout?
        print("Opened serial port:", ser.name) #check which port was really used
        
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
        
                data_to_save = str(serial_input) + "," + str(time_now_epoch) + ","
                
                #save to file
                data_file.write(data_to_save)
                
                #save to Google Drive
                file.GetContentFile("miony_data.txt")
                update = file.GetContentString() + data_to_save 
                file.SetContentString(update)
                file.Upload()
        except KeyboardInterrupt:
            print(">> Ctrl+C pressed, stopped.")
            ser.close()
            data_file.close()
            raise SystemExit
