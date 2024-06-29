# Tests using text file data

import RPi.GPIO as GPIO 
from time import sleep 
from abc import ABC
import SignalDecoder

class TestDataProvider(ABC):
    def InitDataQueue(self, queue):
        self.Queue = queue
        pass

    def ReadFile(self, filename):
        # Open the file
        with open("Tests/" + filename, "r") as file:
            # Read all lines from the file
            lines = file.readlines()
        
        # Loop through each line in the file
        for line in lines:
            print(line)
        
        pass

testProvider = TestDataProvider()
IReader = SignalDecoder.SignalDecoder(testProvider)
testProvider.ReadFile("test-001.txt")

sleep(0.1)
while IReader.hasDetected():
    cmd = IReader.getCommand()
    print(cmd)
    sleep(0.1)


# GPIO_Mode = GPIO.BCM
# GPIO_PIN = 16
# IReader = SignalDecoder.SignalDecoder(SignalDecoder.GPIOEdgeDetectedDataProvider(GPIO_Mode, GPIO_PIN))

