#  MIT License
# 
# Copyright (c) 2024 Felix Biego
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# ______________  _____
# ___  __/___  /_ ___(_)_____ _______ _______
# __  /_  __  __ \__  / _  _ \__  __ `/_  __ \
# _  __/  _  /_/ /_  /  /  __/_  /_/ / / /_/ /
# /_/     /_.___/ /_/   \___/ _\__, /  \____/
#                             /____/


import os
import re
import asyncio
from bleak import BleakScanner, BleakClient


sketch = '''
/*
 * 
 * BLE clone sketch for [NAME]
 * Generated using ble-cloner-arduino
 * developed by fbiego
 * https://github.com/fbiego/ble-cloner-arduino
 * 
 */

#include <NimBLEDevice.h>

class ServerCallbacks : public BLEServerCallbacks
{
	void onConnect(BLEServer *pServer)
	{
		Serial.println("Client connected");
	};
		
	void onDisconnect(BLEServer *pServer)
	{
		Serial.println("Client disconnected - start advertising");
		BLEDevice::startAdvertising();
	};
		
	void onMTUChange(uint16_t MTU, ble_gap_conn_desc *desc)
	{
		Serial.printf("MTU updated: %u for connection ID: %u\\n", MTU, desc->conn_handle);
	};
};

class CharacteristicCallbacks : public BLECharacteristicCallbacks
{
	void onRead(BLECharacteristic *pCharacteristic)
	{
		std::string pData = pCharacteristic->getValue();
		int len = pData.length();
		Serial.print("onRead ");
		Serial.print(pCharacteristic->getUUID().toString().c_str());
		Serial.print(" len ");
		Serial.println(len);
		Serial.print("Data: ");
		for (int i = 0; i < len; i++) {
			Serial.printf("%02X ", pData[i]);
		}
		Serial.println();
	};

	void onWrite(BLECharacteristic *pCharacteristic)
	{
		std::string pData = pCharacteristic->getValue();
		int len = pData.length();
		Serial.print("onWrite ");
		Serial.print(pCharacteristic->getUUID().toString().c_str());
		Serial.print(" len ");
		Serial.println(len);
		Serial.print("Data: ");
		for (int i = 0; i < len; i++) {
			Serial.printf("%02X ", pData[i]);
		}
		Serial.println();
	};

	void onNotify(BLECharacteristic *pCharacteristic)
	{
		std::string pData = pCharacteristic->getValue();
		int len = pData.length();
		Serial.print("onNotify ");
		Serial.print(pCharacteristic->getUUID().toString().c_str());
		Serial.print(" len ");
		Serial.println(len);
		Serial.print("Data: ");
		for (int i = 0; i < len; i++) {
			Serial.printf("%02X ", pData[i]);
		}
		Serial.println();
	};

	void onStatus(BLECharacteristic *pCharacteristic, Status status, int code)
	{
		String str = ("Notification/Indication status code: ");
		str += status;
		str += ", return code: ";
		str += code;
		str += ", ";
		str += BLEUtils::returnCodeToString(code);
		Serial.println(str);
	};

	void onSubscribe(BLECharacteristic *pCharacteristic, ble_gap_conn_desc *desc, uint16_t subValue)
	{
		String str = "Client ID: ";
		str += desc->conn_handle;
		str += " Address: ";
		str += std::string(BLEAddress(desc->peer_ota_addr)).c_str();
		if (subValue == 0)
		{
			str += " Unsubscribed to ";
		}
		else if (subValue == 1)
		{
			str += " Subscribed to notfications for ";
		}
		else if (subValue == 2)
		{
			str += " Subscribed to indications for ";
		}
		else if (subValue == 3)
		{
			str += " Subscribed to notifications and indications for ";
		}
		str += std::string(pCharacteristic->getUUID()).c_str();

		Serial.println(str);
	};
};

class DescriptorCallbacks : public BLEDescriptorCallbacks
{
	void onWrite(BLEDescriptor *pDescriptor)
	{
		Serial.print("Descriptor written:");
		std::string pData = pDescriptor->getValue();
		int len = pData.length();
		for (int i = 0; i < len; i++) {
		  Serial.printf("%02X ", pData[i]);
		}
		Serial.println();
	};

	void onRead(BLEDescriptor *pDescriptor)
	{
		Serial.print(pDescriptor->getUUID().toString().c_str());
		Serial.println("Descriptor read");
	};
};

static DescriptorCallbacks dscCallbacks;
static CharacteristicCallbacks chrCallbacks;

void initBLE()
{
	BLEDevice::init("[NAME]");
	BLEDevice::setMTU(517);
	BLEServer *pServer = BLEDevice::createServer();
	pServer->setCallbacks(new ServerCallbacks());

[SERVICES]

	BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
[ADVERTISING]
	pAdvertising->setScanResponse(true);
	pAdvertising->start();
}

void setup()
{
	Serial.begin(115200);
	initBLE();
	Serial.println("BLE device [NAME] created");
}

void loop()
{
	delay(2000);
}

'''

# Dictionary to cache advertisement data
advertisement_cache = {}

skipService = ['00001800-0000-1000-8000-00805f9b34fb', '00001801-0000-1000-8000-00805f9b34fb']

props = {
		"write-without-response": "NIMBLE_PROPERTY::WRITE_NR",
		"write": "NIMBLE_PROPERTY::WRITE",
		"notify": "NIMBLE_PROPERTY::NOTIFY",
		"read": "NIMBLE_PROPERTY::READ"
}

def advertisement_callback(device, advertisement_data):
    advertisement_cache[device.address] = advertisement_data
    # print(f"Device: {device.name} ({device.address})")
    # print(f"  RSSI: {device.rssi}")
    # print(f"  Advertised Services: {advertisement_data.service_uuids}")
    # for key, value in advertisement_data.manufacturer_data.items():
    #     print(f"  Manufacturer Data: {key}: {value}")
    # for key, value in advertisement_data.service_data.items():
    #     print(f"  Service Data: {key}: {value}")

def clean_string(input_string):
    # Replace spaces with hyphens
    modified_string = input_string.replace(' ', '-')
    
    # Remove characters that are not 0-9, a-z, A-Z, or -
    cleaned_string = re.sub(r'[^0-9a-zA-Z-]', '', modified_string)
    
    return cleaned_string

def convert_uuid(uuid):
    # Convert the input UUID to uppercase
    uuid = uuid.upper()
    # Bluetooth Base UUID
    base_uuid = "00000000-0000-1000-8000-00805F9B34FB"
    # Check if the 128-bit UUID follows the Bluetooth Base UUID format
    if uuid[8:] == base_uuid[8:] and uuid[:4] == base_uuid[:4]:
        # Extract the 16-bit part from the 128-bit UUID
        uuid_16 = uuid[4:8]
        return uuid_16
    else:
        return uuid
def array_hex(byte_array):
    # Convert each byte to a hex string and format it with "0x"
    hex_string = ', '.join(f'0x{byte:02x}' for byte in byte_array)
    return hex_string
def int_hex(value):
    # Ensure the value is within the range of a 16-bit unsigned integer
    if not (0 <= value < 2**16):
        raise ValueError("Value out of range for a 16-bit unsigned integer")

    # Convert the integer to bytes in little-endian order
    byte_array = value.to_bytes(2, byteorder='little')

    # Convert each byte to a hex string and format it with "0x"
    hex_string = ', '.join(f'0x{byte:02x}' for byte in byte_array)
    return hex_string

async def main():
    print("Scanning for BLE devices...")
    print("Listening for advertisements for 10 seconds")

    # Start scanning with a callback to handle advertisement data
    scanner = BleakScanner(detection_callback=advertisement_callback)
    await scanner.start()
    await asyncio.sleep(10)  # Scan for 10 seconds
    await scanner.stop()

    if not advertisement_cache:
        print("No BLE devices found.")
        return

    print("\nFound devices:")
    for i, (address, advertisement_data) in enumerate(advertisement_cache.items()):
        device_name = advertisement_data.local_name or "Unknown"
        print(f"{i}: {device_name} ({address})")

    device_index = int(input("Select a device by index: "))

    if device_index < 0 or device_index >= len(advertisement_cache):
        print("Invalid index")
        return

    selected_address = list(advertisement_cache.keys())[device_index]
    selected_ad_data = advertisement_cache[selected_address]

    # Print the selected device's advertisement data
    print(f"\nSelected Device: {selected_ad_data.local_name} ({selected_address})")
    print(f"  RSSI: {selected_ad_data.rssi}")
    print(f"  Advertised Services: {selected_ad_data.service_uuids}")
    for key, value in selected_ad_data.manufacturer_data.items():
        print(f"  Manufacturer Data: {key}: {value}")
    for key, value in selected_ad_data.service_data.items():
        print(f"  Service Data: {key}: {value}")

    # Find the selected device from the cache
    selected_device = None
    discover_timeout = 30.0
    devices = await BleakScanner.discover(timeout=discover_timeout)
    for device in devices:
        if device.address == selected_address:
            selected_device = device
            break

    if selected_device is None:
        print("Device not found.")
        return

    print(f"\nConnecting to {selected_device.name} ({selected_device.address})")

    folder_name = clean_string(selected_device.name).lower() + "-" + clean_string(selected_device.address).lower()
    file_name = folder_name + ".ino"
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)


    file_path = os.path.join(folder_name, file_name)

    timeout_duration = 120.0

    wServices = ""
    wAdvertising = ""

    async with BleakClient(selected_device, timeout=timeout_duration) as client:
        if not client.is_connected:
            print("Failed to connect")
            return
        

        print(f"Connected to {client.address}")

        services = client.services

        for service in services:
            if service.uuid in skipService:
                continue
            sName = service.uuid.replace('-', '')
            wServices += f"\tBLEService *p{sName} = pServer->createService(\"{convert_uuid(service.uuid)}\");\n"
            for characteristic in service.characteristics:
                pName = characteristic.uuid.replace('-', '')
                nProp = " | \n\t\t".join([props.get(item, item) for item in characteristic.properties])
                wServices += f"\tBLECharacteristic *p{pName} = p{sName}->createCharacteristic(\n\t\t\"{convert_uuid(characteristic.uuid)}\", \n\t\t{nProp});\n"
                wServices += f"\tp{pName}->setCallbacks(&chrCallbacks);\n"
            wServices += "\t\n"

        for service in services:
            if service.uuid in skipService:
                continue
            sName = service.uuid.replace('-', '')
            wServices += f"\tp{sName}->start();\n"
    
    for adService in selected_ad_data.service_uuids:
        wAdvertising += f"\tpAdvertising->addServiceUUID(\"{convert_uuid(adService)}\");\n"
    for key, value in selected_ad_data.manufacturer_data.items():
        # print(f"  Manufacturer Data: {key}: {value}")
        wAdvertising += f"\tuint8_t mData[] = {{{int_hex(key)}, {array_hex(value)}}};\n"
        wAdvertising += f"\tpAdvertising->setManufacturerData(std::string((char *)&mData[0], {2 + len(value)}));\n"
    for key, value in selected_ad_data.service_data.items():
        wAdvertising += f"\tuint8_t sData[] = {{{array_hex(value)}}};\n"
        wAdvertising += f"\tpAdvertising->setServiceData(NimBLEUUID(\"{convert_uuid(key)}\"), std::string((char *)&sData[0], {len(value)}));\n"

    with open(file_path, "w") as file:
        file.write(sketch.replace('[NAME]', selected_device.name).replace('[SERVICES]', wServices).replace('[ADVERTISING]', wAdvertising))
    print(f"Arduino sketch created: {folder_name}")

if __name__ == "__main__":
    asyncio.run(main())


