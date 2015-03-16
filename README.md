nrf51-dfu-ble-S110-hmac-sha256
==============================
Dual/single Bank DFU over BLE (nRF51, S110 v8.x.x)

Based on the dual bank BLE bootloader example in SDKv8.0.0

Init packet has been extended to include a 256-bit SHA256 HMAC (http://en.wikipedia.org/wiki/Hash-based_message_authentication_code) used to verify the authenticity of a firmware image.
HMAC is based on a secret key known only by the trusted entity generating the new firmware image and the nRF51 device.

dfu_init_template.c, now called dfu_init_hmac_sha256.c, was modified in order to add authentication.

Requirements
------------
- nRF51 SDK version 8.0.0
- S110 SoftDevice version 8.x.x
- nRF51-DK

The project may need modifications to work with other versions or other boards. 

To compile it, clone the repository in the nRF51_SDK_8.0.0_5fc2c3a/examples folder.

Secret key
----------
The HMAC implementation is based on a secret key known by both the nRF51 and the entity generating the new firmware image. 
This key should never be part of a new firmware transferred to the nRF51, but rather placed in Flash during production and never changed.
For added safety one could generate one random key per nRF51 and keep track of the BLE address -> key relationship on the backend. 
This has the benefit of having a unique HMAC per device, but requires more logistics (increased complexity often equals reduced security).

Per default, dfu_init_hmac_sha256 expects the secret key  to already be present in UICR. Specifically in the upper part of the CUSTOMER section of UICR (starting at address 0x100010E0).
The included script generates an init packet (.dat) and a key.hex file with the corresponding memory placement, based on an input firmware image and input key. 

How to implement HMAC in bootloader
-----------------------------------
- Add hmac_sha256.c and sha2.c to your object list, and the corresponding header files to your include path
- Replace dfu_init_template.c with dfu_init_hmac_sha256.c
- Adjust the bootloader memory settings in order to accommodate the increased code size (expect increase by 4 flash pages). Note: BOOTLOADER_REGION_START in dfu_types.h must be updated to reflect the new placement. 
- NOTE: If your application is using the persistent storage area right beneath bootloader memory area this must be adjusted as well. 

About this project
------------------
This application is one of several applications that has been built by the support team at Nordic Semiconductor, as a demo of some particular feature or use case. It has not necessarily been thoroughly tested, so there might be unknown issues. It is hence provided as-is, without any warranty. 

However, in the hope that it still may be useful also for others than the ones we initially wrote it for, we've chosen to distribute it here on GitHub. 

The application is built to be used with the official nRF51 SDK, that can be downloaded from http://developer.nordicsemi.com/.

Please post any questions about this project on https://devzone.nordicsemi.com.
