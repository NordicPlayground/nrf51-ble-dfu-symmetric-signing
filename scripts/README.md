Init packet generation script
=============================
This python script generates a DFU init packet (http://developer.nordicsemi.com/nRF51_SDK/nRF51_SDK_v8.x.x/doc/8.0.0/s110/html/a00093.html) and appends a SHA256-based HMAC.

The script follows the same arguments as the Master Control Panel nrf.exe utility with two exceptions.
KEY is a reference to a file containing the 256-bit HMAC key
KEY_OUTPUT is an optional argument to generate a key.hex file suitable to program the device with.

Example of use
==============
The following generates a test.zip file containing application.bin and application.dat (init file) based on the heart rate example hex and example key found in the examples folder:
```
python hmac_init_pkt_gen.py --dev-type 0x1234 \
                            --dev-revision 0xABCD \
                            --application-version 0xDEADBEEF \
                            --key ..\example\example_key.txt \
                            --key-output key.hex \
                            --sd-req 0xFFFE \
                            --application ..\example\nrf51422_xxac_s110_ble_app_hrs.hex \
                            test.zip
```
                            
Note: dummy values are used for device type, revision, and application version. sd-req value 0xFFFE is the "catch all" softdevice for versions

Script arguments
================
```
usage: hmac_init_pkt_gen.py [-h] [--dfu-ver DFU_VER] [--dev-type DEV_TYPE]
                            [--dev-revision DEV_REV]
                            [--application-version APP_VER] --key KEY
                            [--key-output KEY_OUTPUT] --sd-req SD_REQ
                            [--application APPLICATION] [--bootloader BL]
                            [--softdevice SD]
                            zipfile

positional arguments:
  zipfile               The package filename

optional arguments:
  -h, --help            show this help message and exit
  --dfu-ver DFU_VER     DFU packet version to use
  --dev-type DEV_TYPE   Device type
  --dev-revision DEV_REV
                        Device revision
  --application-version APP_VER
                        Application version
  --key KEY             Name of key file to use for encrypting the package
  --key-output KEY_OUTPUT
                        Name of file to use if key is to be written to .hex
  --sd-req SD_REQ       SoftDevice requirement. What SoftDevice is required to
                        already be present on the target device. Should be a
                        list of firmware IDs. Example: --sd-req 0x4F,0x5A. Use
                        0xFFFE to support all SoftDevicesSee: http://developer
                        .nordicsemi.com/nRF51_SDK/nRF51_SDK_v8.x.x/doc/8.0.0/s
                        110/html/a00093.html
  --application APPLICATION
                        The application firmware .hex file
  --bootloader BL       The bootloader firmware .hex file
  --softdevice SD       The SoftDevice firmware .hex file
  ```