/*
overflow
RTC -> ESP32_RTC_CLK_SRC_INT_8MD256
*/

#include <Arduino.h>
#include "SD_MMC.h"
#include "FS.h"
#include <sys/time.h>

#define inputPin 16
#define timeout 24000 // for 100us at 240MHz clock

volatile unsigned long timeA;
volatile unsigned long timeB;
volatile unsigned long dTime;
volatile int wasInterrupt = 0;
int file_counter = 0;
int counter = 0;
int unsigned long total_count = 0;
int new_file_threshold = 2000;
int serial_in_data = 0;
bool debug = false;

void IRAM_ATTR isr(){
    timeA = ESP.getCycleCount();  // Overflow every ~28s
    wasInterrupt = 1;
}

void writeFile(fs::FS &fs, const char * path, const char * message){
    if(debug){Serial.printf("Writing file: %s\n", path);}

    File file = fs.open(path, FILE_WRITE);
    if(!file){
        if(debug){Serial.println("Failed to open file for writing");}
        return;
    }
    if(file.print(message)){
        if(debug){Serial.println("File written");}
    }else{
        Serial.println("Write failed");
    }
}

void appendFile(fs::FS &fs, const char * path, const char * message){
    //Serial.printf("Appending to file: %s\n", path);

    File file = fs.open(path, FILE_APPEND);
    if(!file){
        Serial.println("Failed to open file for appending");
        return;
    }
    if(file.print(message)){
        if(debug){Serial.println("Message appended");}
    }else{
        Serial.println("Append failed");
    }
}

void readFile(fs::FS &fs, const char * path){
    Serial.printf("Reading file: %s\n", path);

    File file = fs.open(path);
    if(!file){
        Serial.println("Failed to open file for reading");
        return;
    }

    if(debug){Serial.print("Read from file: ");}
    while(file.available()){
	    Serial.write(file.read());
    }
}

void createDir(fs::FS &fs, const char * path){
    if(debug){Serial.printf("Creating Dir: %s\n", path);}
    if(fs.mkdir(path)){
        if(debug){Serial.println("Dir created");}
    }else{
        Serial.println("mkdir failed");
    }
}

void deleteFile(fs::FS &fs, const char * path){
    if(debug){Serial.printf("Deleting file: %s\n", path);}
    if(fs.remove(path)){
        if(debug){Serial.println("File deleted");}
    } else {
        Serial.println("Delete failed");
    }
}

//Source: https://github.com/markszabo/IRremoteESP8266/blob/master/src/IRutils.cpp#L48
String uint64ToString(uint64_t input) {
  String result = "";
  uint8_t base = 10;

  do {
    char c = input % base;
    input /= base;

    if (c < 10)
      c +='0';
    else
      c += 'A' - 10;
    result = c + result;
  } while (input);
  return result;
}


void setup(){
    pinMode(inputPin, INPUT);
    attachInterrupt(inputPin, isr, RISING);
    Serial.begin(115200);
    
    if(!SD_MMC.begin()){
        Serial.println("Card Mount Failed");
        return;
    }

    uint8_t cardType = SD_MMC.cardType();
    if(cardType == CARD_NONE){
        Serial.println("No SD card attached");
        return;
    }
    if(!SD_MMC.exists("/data")){
        createDir(SD_MMC, "/data");
    }

    //load counter, file_counter ad totalcout values from SD card
    if(SD_MMC.exists("/data/counter.txt")){
        File file = SD_MMC.open("/data/counter.txt");
        
        if(!file){
            Serial.println("Failed to open file for reading counter value!");
            return;
        }

        counter = String(file.read()).toInt();
        
        Serial.println("Counter value loaded successfully!");
    }

    if(SD_MMC.exists("/data/file_counter.txt")){
        File file = SD_MMC.open("/data/file_counter.txt");
        
        if(!file){
            Serial.println("Failed to open file for reading counter value!");
            return;
        }

        file_counter = String(file.read()).toInt();
        
        Serial.println("Counter_file value loaded successfully!");
    }

    if(SD_MMC.exists("/data/total_count.txt")){
        File file = SD_MMC.open("/data/total_count.txt");
        
        if(!file){
            Serial.println("Failed to open file for reading total_count value!");
            return;
        }

        total_count = String(file.read()).toInt();
        
        Serial.println("Toral_count value loaded successfully!");
    }

    Serial.println("Initialized!");
}

void loop() {
    if(wasInterrupt == 1){
        timeB = timeA;
        timeA = 0;

        while(ESP.getCycleCount() < timeB + timeout){
            if (timeA != 0){
                dTime = timeA - timeB;
                Serial.println(dTime);

                if((SD_MMC.usedBytes() / (1024*1024) > 100)){
                    if(counter == new_file_threshold){
                        file_counter ++;
                        counter = 0;
                        //save file_counter value to SD card
                         if(SD_MMC.exists("/data/file_counter.txt")){
                            deleteFile(SD_MMC, "/data/file_counter.txt");
                        }
                        writeFile(SD_MMC, "/data/file_counter.txt", (String(file_counter)).c_str());
                        
                        //save counter value to SD card
                        if(SD_MMC.exists("/data/counter.txt")){
                            deleteFile(SD_MMC, "/data/counter.txt");
                        }
                        writeFile(SD_MMC, "/data/counter.txt", (String(counter)).c_str());
                    }     

                    String path = "/data/" + String(file_counter) + ".csv";  

                    if(SD_MMC.exists(path)){
                        appendFile(SD_MMC, path.c_str(), (String(dTime) + "," + uint64ToString(esp_timer_get_time()) + ",").c_str());
                    }else{
                        writeFile(SD_MMC, path.c_str(), (String(dTime) + "," + uint64ToString(esp_timer_get_time()) + ",").c_str());
                    }
                    counter ++;
                    total_count ++;
                }else{
                    Serial.print("SD card is full");
                    exit(0);
                }

                //save counter value to SD card
                if(SD_MMC.exists("/data/counter.txt")){
                    deleteFile(SD_MMC, "/data/counter.txt");
                }
                writeFile(SD_MMC, "/data/counter.txt", (String(counter)).c_str());
                
                //save total_count to SD card
                if(SD_MMC.exists("/data/total_count.txt")){
                    deleteFile(SD_MMC, "/data/total_count.txt");
                }
                writeFile(SD_MMC, "/data/total_count.txt", (String(total_count)).c_str());
               
                wasInterrupt = 0; // <------------ too late?
                break;
            }
        }
    }
 
    if(Serial.available()){
        serial_in_data = Serial.read();
        serial_in_data -= 48;
        Serial.print(serial_in_data);
        if(serial_in_data == 1){ //print data <------------------------
            Serial.println("Printing data:");
            if(file_counter < 100000){
                for(int i = 0; i <= file_counter; i++){
                    String open_path = "/data/" + String(i) + ".csv";
                    readFile(SD_MMC, open_path.c_str());
                }
            }   
        }else if(serial_in_data == 2){ //print total_count
            Serial.println(total_count);
        }else if(serial_in_data == 3){ //print time since boot
            Serial.println("time_since_boot:" + uint64ToString(esp_timer_get_time()) + "us");
        }else if(serial_in_data == 7){ //debug mode on/off
            debug = !debug;
            if(debug){
                Serial.println("Debug mode on!");
            }else{
                Serial.println("Debug mode off!");
            }
        }else if(serial_in_data == 8){ //reset counter values
            //zero file_counter value and save to SD card
            if(SD_MMC.exists("/data/file_counter.txt")){
                deleteFile(SD_MMC, "/data/file_counter.txt");
            }
            writeFile(SD_MMC, "/data/file_counter.txt", "0");
                        
            //zero counter value and save to SD card
            if(SD_MMC.exists("/data/counter.txt")){
                deleteFile(SD_MMC, "/data/counter.txt");
            }
            writeFile(SD_MMC, "/data/counter.txt", "0");

            //zero total_count and save to SD card
            if(SD_MMC.exists("/data/total_count.txt")){
                deleteFile(SD_MMC, "/data/total_count.txt");
            }
            writeFile(SD_MMC, "/data/total_count.txt", "0");

            Serial.println("counter values reset!");
        }else if(serial_in_data == 9){ //restart
            Serial.println("Restarting");
            ESP.restart();
        }else{
            Serial.println("Unknown command");
        }
    serial_in_data = 0;
    }
}