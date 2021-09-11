# NEC-Decoder

Designed and tested on Raspberry PI Zero
Version 0.1 under tests

The idea of this module is to retrieve, translate and fill in missing InfraRed signal for Raspberry PI 
Raspberry is convenient device, but has unreliable signal retrieving speed.

This module try to guess missing signal phrases.

Before using make sure your Raspberry PI has
- appropriate power adapter
- good cooling

Additionally, follow IR Receiver documentation to use appropriate resistors to eliminate unnecessary noises

Use case example:

# Example
IReader = IRdecoder()

while True:
    sleep(0.1)
    
    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)
