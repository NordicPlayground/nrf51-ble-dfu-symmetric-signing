Init packet generation script
=============================
This python script generates a DFU init packet (http://developer.nordicsemi.com/nRF51_SDK/doc/7.2.0/s110/html/a00065.html) and appends a SHA256-based HMAC.
Both the init packet and a key.hex file

The init packet is based on a configuration file, as is the secret key used by the HMAC.
Examples of both are found in ../example

The following command generates an init packet based on the example files and a heart rate example from SDK v7.2.0:

$ python hmac_init_pkt_gen.py ../example/nrf51422_xxac_s110_ble_app_hrs.bin ../example/example_key.txt ../example/example_init_data.txt init_pkt.dat key.hex