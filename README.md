# NEC-Decoder

Designed and tested on Raspberry PI Zero
Version 0.1
Python 3 required

The idea of this module is to retrieve, translate and fill in missing InfraRed signal for Raspberry PI 

IR Signal recorded by a sound card using Line-in looks like this one:
![Recorded IR Signal](https://github.com/kamilskoczylas/NEC-Decoder/blob/main/RecordedIRsignal.jpg?raw=true)
- 9 miliseconds of positive signal
- 4.5 miliseconds of negative
- 27 miliseconds 8-bit Address and 8-bit of inversed address
- 27 miliseconds 8-bit Command and 8-bit inversed command

Example from the recording:
- Address: 00000000 11111111
- Command: 10100010 01011101

---
Requirements
-

Before using with Raspberry Zero make sure your Raspberry PI has
- appropriate power adapter
- good cooling
- use Python 3

Additionally, follow IR Receiver documentation to use appropriate resistors to eliminate unnecessary noises

---
Example
-

```    
# Only for value of GPIO.BCM
import RPi.GPIO as GPIO 
from time import sleep 

import NEC
import SignalDecoder
import GPIODataProvider

GPIO_Mode = GPIO.BCM
GPIO_PIN = 16

# Initialization of the class. Sets thread deamon
# Default values are GPIO.BCM and PIN 16
IReader = SignalDecoder.SignalDecoder(
    GPIODataProvider.EdgeDetected(
        GPIO_Mode,
        GPIO_PIN
    ),
    NEC.NECDecoder()
    )

while True:
    sleep(0.1)

    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)
```
