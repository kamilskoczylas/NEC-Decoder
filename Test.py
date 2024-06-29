# Tests using text file data

import RPi.GPIO as GPIO 
from time import sleep 
from timeit import default_timer
import datetime
from abc import ABC
import SignalDecoder

class TestDataProvider(ABC):
    def InitDataQueue(self, queue):
        self.Queue = queue
        pass

    def ReadFile(self, filename):
        with open("Tests/" + filename, "r") as file:
            lines = file.readlines()
            
        timeline = False
        edge_number = 0
        for line in lines:
            if 'Timeline' in line:
                timeline = True
                edge_number = 0
                previous_signal = default_timer()
                
            if timeline:
                words = line.split()
                print(words)
                edge_number += 1
                if int(words[0]) == edge_number:
                    time_delta = datetime.timedelta(0, float(words[1]))
                    previous_signal += time_delta
                    self.Queue.put_nowait(previous_signal)
                else:
                    timeline = False
            else:
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

