/*
Note:
    overflow of ESP.getCycleCount()
    assuming SD card is not full
    assuming wifi is always connected

To do:
    rename file instead of deleting

SD card file structure:
/data
    - data.csv
    - counter.txt 
    - time_start.txt

SD card -> ESP32
 CS         5
 SCK        18
 MOSI       23
 MISO       19
*/

// option select
#define wifi


#include <Arduino.h>
#include <SD.h>
#include <time.h>


#ifdef wifi
    #include <WiFi.h>
    #include <NTPClient.h>
    #include <WiFiUdp.h>
    #include "Credentials.h"

    #define UTC_OFFSET_IN_SECONDS 3600 // offset from Greenwitch time
    #define NTP_TIME_UPDATE_INTERVAL 60000 // 1 minute

    #ifdef CREDENTIALS_H
        char ssid[] = WIFI_SSID;
        char password[] = WIFI_PASSWORD;
    #else
        char ssid[] = "sample_ssid";
        char password[] = "sample_password";
    #endif

    WiFiUDP ntpUDP;
    NTPClient timeClient(ntpUDP, "cz.pool.ntp.org", UTC_OFFSET_IN_SECONDS, NTP_TIME_UPDATE_INTERVAL);
#endif


#define INPUT_PIN 16
#define OUTPUT_PIN 33
#define TIMEOUT 12000 // for 50 μs at 240MHz clock
#define BAUD_RATE 115200


volatile unsigned long time_a;
volatile unsigned long time_b;
volatile unsigned long d_time;
volatile bool interrupt_flag = false;
int counter = 0;
int serial_in_data = 0;



void IRAM_ATTR isr()
{
    time_a = ESP.getCycleCount(); // overflow every ~28s
    interrupt_flag = true;
}

// Source: https://github.com/markszabo/IRremoteESP8266/blob/master/src/IRutils.cpp#L48
String uint64_to_string(uint64_t input)
{
    String result = "";
    uint8_t base = 10;

    do
    {
        char c = input % base;
        input /= base;

        if (c < 10)
            c += '0';
        else
            c += 'A' - 10;
        result = c + result;
    } while (input);
    return result;
}

void write_file(fs::FS &fs, const char *path, const char *message)
{

    //Serial.printf("Writing file: %s\n", path);

    File file = fs.open(path, FILE_WRITE);
    if (!file)
    {
        Serial.println("Failed to open file for writing");
        return;
    }

    if (file.print(message))
    {
        //Serial.println("File written");
    }
    else
    {
        Serial.println("Write failed");
    }

    file.close();
}

void append_file(fs::FS &fs, const char *path, const char *message)
{

    //Serial.printf("Appending to file: %s\n", path);

    File file = fs.open(path, FILE_APPEND);
    if (!file)
    {
        Serial.println("Failed to open file for appending");
        return;
    }

    if (file.print(message))
    {
        //Serial.println("Message appended");
    }
    else
    {
        Serial.println("Append failed");
    }

    file.close();
}

void readFile(fs::FS &fs, const char *path)
{

    Serial.printf("Reading file: %s\n", path);

    File file = fs.open(path);
    if (!file)
    {
        Serial.println("Failed to open file for reading");
        return;
    }

    //Serial.print("Read from file: ");
    while (file.available())
    {
        Serial.write(file.read());
    }

    file.close();
}

void createDir(fs::FS &fs, const char *path)
{

    //Serial.printf("Creating Dir: %s\n", path);

    if (fs.mkdir(path))
    {
        //Serial.println("Dir created");
    }
    else
    {
        Serial.println("mkdir failed");
    }
}

void delete_file(fs::FS &fs, const char *path)
{

    //Serial.printf("Deleting file: %s\n", path);

    if (fs.remove(path))
    {
        //Serial.println("File deleted");
    }
    else
    {
        Serial.println("Delete failed");
    }
}

void setup()
{
    // IO pins setup
    pinMode(INPUT_PIN, INPUT);
    attachInterrupt(INPUT_PIN, isr, RISING);
    pinMode(OUTPUT_PIN, OUTPUT);

    Serial.begin(BAUD_RATE);

    // SD card setup
    if (!SD.begin())
    {
        Serial.println("Card Mount Failed");
        return;
    }

    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE)
    {
        Serial.println("No SD card attached");
        return;
    }
    if (!SD.exists("/data"))
    {
        createDir(SD, "/data");
    }

    // load counter value from SD card
    if (SD.exists("/data/counter.txt"))
    {
        File file = SD.open("/data/counter.txt");

        if (!file)
        {
            Serial.println("Failed to open file for reading counter value!");
            return;
        }

        counter = String(file.read()).toInt();

        Serial.println("Counter value loaded successfully!");
    }

    #ifdef wifi
    WiFi.begin(ssid, password);

    while(WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    timeClient.begin();
    timeClient.update();
    delay(500);
    Serial.println("Started at: " + String(timeClient.getFormattedTime()));
    
    // save startup time
    write_file(SD, "/data/startup_time.txt", (String(timeClient.getEpochTime())).c_str());
    #endif
}



void loop()
{
    if (interrupt_flag)
    {
        time_b = time_a;
        time_a = 0;

        while (ESP.getCycleCount() < time_b + TIMEOUT)
        {
            if (time_a != 0)
            {
                digitalWrite(OUTPUT_PIN, HIGH);
                d_time = time_a - time_b;
                Serial.println(d_time);

                if (SD.exists("/data/data.csv"))
                {
                    append_file(SD, "/data/data.csv", ("\n" + String(d_time) + "," + uint64_to_string(esp_timer_get_time()) + "," + String(timeClient.getEpochTime())).c_str());
                }
                else
                {
                    write_file(SD, "/data/data.csv", (String(d_time) + "," + uint64_to_string(esp_timer_get_time()) + "," + String(timeClient.getEpochTime())).c_str());
                }
                counter++;

                // save counter value to SD card
                if (SD.exists("/data/counter.txt"))
                {
                    delete_file(SD, "/data/counter.txt");
                }
                write_file(SD, "/data/counter.txt", (String(counter)).c_str());
                digitalWrite(OUTPUT_PIN, LOW);
                interrupt_flag = false; // <------------ too late?
                break;
            }
        }
    }

    if (Serial.available())
    {
        serial_in_data = Serial.read();
        serial_in_data -= 48;
        Serial.println(serial_in_data);
        if (serial_in_data == 1)
        { // print data
            Serial.println("Printing data:");
            readFile(SD, "/data/data.csv");
            Serial.print("\n");
        }
        else if (serial_in_data == 2)
        { // print counter
            Serial.println("Count is: " + String(counter));
        }
        else if (serial_in_data == 3)
        { // print time since boot
            Serial.println("Time_since_boot is : " + uint64_to_string(esp_timer_get_time()) + "us");
            // print time
            Serial.println("Current epoch time + offset is: " + String(timeClient.getEpochTime()) + " aka time: " + String(timeClient.getFormattedTime()));
        }
        else if (serial_in_data == 8)
        { // reset counter value
            // zero counter value and save to SD card
            if (SD.exists("/data/counter.txt"))
            {
                delete_file(SD, "/data/counter.txt");
            }
            write_file(SD, "/data/counter.txt", "0");

            counter = 0;

            Serial.println("counter value reset!");
        }
        else if (serial_in_data == 9)
        { // restart
            Serial.println("Restarting");
            ESP.restart();
        }
        else if (serial_in_data == -6)
        {
            Serial.println("Deleting data!");
            delete_file(SD, "/data/data.csv");

            if (SD.exists("/data/counter.txt"))
            {
                delete_file(SD, "/data/counter.txt");
            }
            write_file(SD, "/data/counter.txt", "0");

            counter = 0;

            Serial.println("counter value reset!");
        }
        else
        {
            Serial.println("Unknown command");
        }
        serial_in_data = 0;
    }
}