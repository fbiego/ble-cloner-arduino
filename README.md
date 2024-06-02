# BLE Cloner for Arduino

This project provides a Python script to clone the services, characteristics, and advertising data of a BLE device. It then generates an Arduino sketch that, when flashed to an ESP32, emulates the original BLE device using the NimBLE library.

## Prerequisites

Before running the script, ensure you have the `bleak` library installed:

```bash
pip install bleak
```
## Running the Script

To run the script, execute the following command in your terminal:

```bash
python ble.py
```

## Usage

1. **Scan for BLE Devices**: 
    - The script will scan for BLE devices for 10 seconds and display a list of found devices.

2. **Select a Device**: 
    - Choose the device you want to clone by entering its index from the displayed list.

3. **Generate Arduino Sketch**: 
    - After selecting the device, an Arduino sketch will be created with the same services, characteristics, and advertising data as the original device.

## Flashing the Sketch

1. **Open Arduino IDE**: 
    - Open the generated Arduino sketch in the Arduino IDE.

2. **Connect ESP32**: 
    - Connect your ESP32 to your computer.

3. **Select Board and Port**: 
    - In the Arduino IDE, select the appropriate board (e.g., ESP32 Dev Module) and port.

4. **Upload Sketch**: 
    - Upload the sketch to your ESP32.

This will create a BLE device on the ESP32 with similar services, characteristics, and advertising data as the cloned device.


## Example Output

After running the script and selecting a device, you will see the cloned services, characteristics, and advertising data printed in the console. An Arduino sketch file will be generated that you can use with the ESP32.
