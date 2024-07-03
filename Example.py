# Only for value of GPIO.BCM
import RPi.GPIO as GPIO 
from time import sleep 

import NEC
import SignalDecoder
import GPIODataProvider

GPIO_Mode = GPIO.BCM
GPIO_PIN = 16

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
