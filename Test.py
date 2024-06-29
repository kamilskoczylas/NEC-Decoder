# Tests using text file data

# Only for value of GPIO.BCM
import RPi.GPIO as GPIO 
# Sleeping allows CPU to increase performance for other applications on Raspberry
# CPU goes down from 100% to 5-15% on NECDecoder
from time import sleep 

from SignalDecoder import SignalDecoder

GPIO_Mode = GPIO.BCM
GPIO_PIN = 16

# Initialization of the class. Sets thread deamon
# Default values are GPIO.BCM and PIN 16
IReader = SignalDecoder(GPIO_Mode, GPIO_PIN)

while True:
    sleep(0.1)

    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)
