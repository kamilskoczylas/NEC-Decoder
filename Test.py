# Tests using text file data

import RPi.GPIO as GPIO 
from time import sleep 

from SignalDecoder import SignalDecoder

GPIO_Mode = GPIO.BCM
GPIO_PIN = 16

# Initialization of the class. Sets thread deamon
# Default values are GPIO.BCM and PIN 16
IReader = SignalDecoder(GPIOEdgeDetectedDataProvider(GPIO_Mode, GPIO_PIN))

while True:
    sleep(0.1)

    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)
