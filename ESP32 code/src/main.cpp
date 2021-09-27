/*
overflow of ESP.getCycleCount()
asuming SD card is not full
add rtc time of restart for compensation
external RTC or accept ~5% drift
*/

/*
SD card file structure:
/data
    - data.csv
    - counter.txt  
*/

#include <Arduino.h>
#include <SD.h>
#include <sys/time.h>

#define input_pin 16
#define timeout 24000 // for 100us at 240MHz clock
#define baud_rate 115200

//#define debug

volatile unsigned long time_a;
volatile unsigned long time_b;
volatile unsigned long d_time;
volatile bool interrupt_flag = false;
int counter = 0;
int serial_in_data = 0;
struct timeval tv_now;

void IRAM_ATTR isr()
{
    time_a = ESP.getCycleCount(); // Overflow every ~28s
    interrupt_flag = true;
}

//Source: https://github.com/markszabo/IRremoteESP8266/blob/master/src/IRutils.cpp#L48
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
    // input_pin setup
    pinMode(input_pin, INPUT);
    attachInterrupt(input_pin, isr, RISING);

    Serial.begin(baud_rate);

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

    //load counter value from SD card
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

    Serial.println("Initialized!");
}

#ifdef debug
void loop()
{
    /*
    d_time = 123456789;
    Serial.println(d_time);

    if (SD.exists("/data/data.csv"))
    {
        append_file(SD, "/data/data.csv", (String(d_time) + "," + uint64_to_string(esp_timer_get_time()) + ",").c_str());
    }
    else
    {
        write_file(SD, "/data/data.csv", (String(d_time) + "," + uint64_to_string(esp_timer_get_time()) + ",").c_str());
    }
    counter++;

    //save counter value to SD card
    if (SD.exists("/data/counter.txt"))
    {
        delete_file(SD, "/data/counter.txt");
    }
    write_file(SD, "/data/counter.txt", (String(counter)).c_str());

    d_time++;
    delay(5000);*/

    if (Serial.available())
    {
        serial_in_data = Serial.read();
        serial_in_data -= 48;
        Serial.println(serial_in_data);
        if (serial_in_data == 1)
        { //print data
            Serial.println("Printing data:");
            readFile(SD, "/data/data.csv");
        }
        else if (serial_in_data == 2)
        { //print counter
            Serial.println(counter);
        }
        else if (serial_in_data == 3)
        { //print time since boot
            Serial.println("time_since_boot:" + uint64_to_string(esp_timer_get_time()) + "us");
        }
        else if (serial_in_data == 8)
        { // reset counter value and save to SD card

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
        else
        {
            Serial.println("Unknown command");
        }
        serial_in_data = 0;
    }
}
#else
void loop()
{
    if (interrupt_flag)
    {
        time_b = time_a;
        time_a = 0;

        while (ESP.getCycleCount() < time_b + timeout)
        {
            if (time_a != 0)
            {
                d_time = time_a - time_b;
                Serial.println(d_time);

                if (SD.exists("/data/data.csv"))
                {
                    append_file(SD, "/data/data.csv", (String(d_time) + "," + uint64_to_string(esp_timer_get_time()) + ",").c_str());
                }
                else
                {
                    write_file(SD, "/data/data.csv", (String(d_time) + "," + uint64_to_string(esp_timer_get_time()) + ",").c_str());
                }
                counter++;

                //save counter value to SD card
                if (SD.exists("/data/counter.txt"))
                {
                    delete_file(SD, "/data/counter.txt");
                }
                write_file(SD, "/data/counter.txt", (String(counter)).c_str());

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
        { //print data <------------------------
            Serial.println("Printing data:");
            readFile(SD, "/data/data.csv");
        }
        else if (serial_in_data == 2)
        { //print counter
            Serial.println(counter);
        }
        else if (serial_in_data == 3)
        { //print time since boot
            Serial.println("time_since_boot:" + uint64_to_string(esp_timer_get_time()) + "us");
        }
        else if (serial_in_data == 8)
        { //reset counter values
            //zero counter value and save to SD card
            if (SD.exists("/data/counter.txt"))
            {
                delete_file(SD, "/data/counter.txt");
            }
            write_file(SD, "/data/counter.txt", "0");

            counter = 0;

            Serial.println("counter value reset!");
        }
        else if (serial_in_data == 9)
        { //restart
            Serial.println("Restarting");
            ESP.restart();
        }
        else
        {
            Serial.println("Unknown command");
        }
        serial_in_data = 0;
    }
}
#endif