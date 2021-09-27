echo 'Does not work on WSL!'
cp ../'ESP32 code'/.pio/build/esp32dev/firmware.bin ./firmware.bin
cp ../'ESP32 code'/.pio/build/esp32dev/partitions.bin ./partitions.bin
mkdir esptool
git clone https://github.com/espressif/esptool ./esptool
python3 ./esptool/esptool.py --chip esp32 --port "/dev/ttyUSB0" --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 bootloader_dio_40m.bin 0x8000 partitions.bin 0xe000 boot_app0.bin 0x10000 firmware.bin